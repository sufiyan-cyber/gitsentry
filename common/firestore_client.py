"""Firestore Memory Bank client for GitSentry.

Manages CRUD operations for the three Firestore collections defined in the PRD:
  - projects/{repo_id}/decisions/{decision_id}
  - projects/{repo_id}/dev_habits/{author_id}
  - projects/{repo_id}/audit_log/{event_id}
  - projects/{repo_id}/memory_briefs/latest

Supports both live Firestore and a fully in-memory mock for local development and testing.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from common.config import Settings, get_settings
from common.models import (
    AuditLogDocument,
    DecisionDocument,
    DecisionStatus,
    DevHabitDocument,
    MemoryBrief,
)

logger = logging.getLogger(__name__)


class MockDocumentReference:
    """Lightweight stand-in for a Firestore DocumentReference in test/local mode."""

    def __init__(self, path: str, data: Optional[dict] = None):
        self.path = path
        self.id = path.rsplit("/", 1)[-1] if "/" in path else path
        self._data = data

    def get(self):
        return self

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return self._data or {}


class FirestoreMemoryBank:
    """Manages all Firestore Memory Bank operations.

    In test or local dev mode (when Firestore is unavailable), operates against
    an in-memory dict so that every other layer can be integration-tested
    without a running Firestore emulator.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._client = None
        self._initialized = False
        # In-memory store for test/local: { "collection_path": { "doc_id": dict } }
        self._mock_store: Dict[str, Dict[str, dict]] = {}
        self._use_mock = self.settings.is_test or not self._try_init_client()

    def _try_init_client(self) -> bool:
        """Attempts to initialise the live Firestore client.  Returns True on success."""
        if self._initialized:
            return self._client is not None
        self._initialized = True
        try:
            from google.cloud import firestore as firestore_lib

            self._client = firestore_lib.Client(
                project=self.settings.GCP_PROJECT_ID,
                database=self.settings.FIRESTORE_DATABASE,
            )
            logger.info("Firestore client initialised for project %s", self.settings.GCP_PROJECT_ID)
            return True
        except Exception as exc:
            logger.warning("Firestore client unavailable (%s) — using in-memory mock", exc)
            self._client = None
            return False

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _collection_path(self, repo_id: str, sub: str) -> str:
        return f"projects/{repo_id}/{sub}"

    def _set_doc(self, collection_path: str, doc_id: str, data: dict) -> str:
        if self._use_mock:
            self._mock_store.setdefault(collection_path, {})[doc_id] = data
            logger.debug("[Mock] Set %s/%s", collection_path, doc_id)
            return doc_id
        col_ref = self._client.collection(collection_path)
        col_ref.document(doc_id).set(data)
        logger.debug("Firestore SET %s/%s", collection_path, doc_id)
        return doc_id

    def _get_doc(self, collection_path: str, doc_id: str) -> Optional[dict]:
        if self._use_mock:
            return self._mock_store.get(collection_path, {}).get(doc_id)
        doc_ref = self._client.collection(collection_path).document(doc_id)
        snap = doc_ref.get()
        return snap.to_dict() if snap.exists else None

    def _list_docs(self, collection_path: str, limit: int = 500) -> List[dict]:
        if self._use_mock:
            return list(self._mock_store.get(collection_path, {}).values())[:limit]
        docs = []
        for snap in self._client.collection(collection_path).limit(limit).stream():
            d = snap.to_dict()
            d["_doc_id"] = snap.id
            docs.append(d)
        return docs

    def _count_docs(self, collection_path: str) -> int:
        if self._use_mock:
            return len(self._mock_store.get(collection_path, {}))
        # Firestore aggregation query
        try:
            col_ref = self._client.collection(collection_path)
            count_query = col_ref.count()
            results = count_query.get()
            return results[0][0].value if results else 0
        except Exception:
            # Fallback: stream and count
            return sum(1 for _ in self._client.collection(collection_path).stream())

    def _update_doc(self, collection_path: str, doc_id: str, updates: dict):
        if self._use_mock:
            existing = self._mock_store.get(collection_path, {}).get(doc_id, {})
            existing.update(updates)
            self._mock_store.setdefault(collection_path, {})[doc_id] = existing
            return
        self._client.collection(collection_path).document(doc_id).update(updates)

    def _delete_doc(self, collection_path: str, doc_id: str):
        if self._use_mock:
            self._mock_store.get(collection_path, {}).pop(doc_id, None)
            return
        self._client.collection(collection_path).document(doc_id).delete()

    # ------------------------------------------------------------------
    # Decisions CRUD
    # ------------------------------------------------------------------

    def add_decision(self, repo_id: str, decision: DecisionDocument) -> str:
        """Writes a new decision document.  Returns the generated doc ID."""
        col = self._collection_path(repo_id, "decisions")
        doc_id = f"dec-{uuid.uuid4().hex[:12]}"
        data = decision.model_dump(mode="json")
        # Ensure datetime serialisation is a string
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = v.isoformat()
        self._set_doc(col, doc_id, data)
        logger.info("Added decision %s to repo %s: %s", doc_id, repo_id, decision.description[:80])
        return doc_id

    def get_active_decisions(self, repo_id: str) -> List[DecisionDocument]:
        """Returns all decisions with status 'active' for a repo."""
        col = self._collection_path(repo_id, "decisions")
        raw_docs = self._list_docs(col)
        results: List[DecisionDocument] = []
        for raw in raw_docs:
            try:
                doc = DecisionDocument(**raw)
                if doc.status == DecisionStatus.ACTIVE:
                    results.append(doc)
            except Exception as exc:
                logger.warning("Skipping malformed decision doc: %s", exc)
        return results

    def get_all_decisions(self, repo_id: str) -> List[DecisionDocument]:
        """Returns every decision for a repo (active + superseded)."""
        col = self._collection_path(repo_id, "decisions")
        raw_docs = self._list_docs(col)
        results: List[DecisionDocument] = []
        for raw in raw_docs:
            try:
                results.append(DecisionDocument(**raw))
            except Exception as exc:
                logger.warning("Skipping malformed decision doc: %s", exc)
        return results

    def supersede_decision(self, repo_id: str, doc_id: str):
        """Marks a decision as superseded."""
        col = self._collection_path(repo_id, "decisions")
        self._update_doc(col, doc_id, {"status": DecisionStatus.SUPERSEDED.value})

    def count_decisions(self, repo_id: str) -> int:
        return self._count_docs(self._collection_path(repo_id, "decisions"))

    # ------------------------------------------------------------------
    # Dev Habits CRUD
    # ------------------------------------------------------------------

    def upsert_dev_habit(
        self,
        repo_id: str,
        author_id: str,
        pattern: str,
        pr_reference: str,
    ) -> DevHabitDocument:
        """Creates or updates a dev_habits entry for an author.

        If a habit document with a matching pattern already exists for this
        author, the occurrence is appended and last_seen is updated.
        Otherwise a new document is created.
        """
        col = self._collection_path(repo_id, "dev_habits")
        # The doc ID is deterministic per (author, pattern-hash) for idempotent upserts
        pattern_key = pattern.lower().replace(" ", "_")[:40]
        doc_id = f"{author_id}__{pattern_key}"

        existing = self._get_doc(col, doc_id)
        now = datetime.now(timezone.utc)

        if existing:
            occurrences = existing.get("occurrences", [])
            if pr_reference not in occurrences:
                occurrences.append(pr_reference)
            self._update_doc(col, doc_id, {
                "occurrences": occurrences,
                "last_seen": now.isoformat(),
            })
            existing["occurrences"] = occurrences
            existing["last_seen"] = now.isoformat()
            habit = DevHabitDocument(**existing)
            logger.info(
                "Updated dev habit for %s (count=%d): %s",
                author_id, len(occurrences), pattern[:60],
            )
        else:
            habit = DevHabitDocument(
                pattern=pattern,
                occurrences=[pr_reference],
                first_seen=now,
                last_seen=now,
            )
            data = habit.model_dump(mode="json")
            for k, v in data.items():
                if isinstance(v, datetime):
                    data[k] = v.isoformat()
            self._set_doc(col, doc_id, data)
            logger.info("Created dev habit for %s: %s", author_id, pattern[:60])

        return habit

    def get_author_habits(self, repo_id: str, author_id: str) -> List[DevHabitDocument]:
        """Returns all dev_habits entries whose doc ID starts with the author's login."""
        col = self._collection_path(repo_id, "dev_habits")
        if self._use_mock:
            store = self._mock_store.get(col, {})
            results = []
            for doc_id, raw in store.items():
                if doc_id.startswith(f"{author_id}__"):
                    try:
                        results.append(DevHabitDocument(**raw))
                    except Exception:
                        pass
            return results
        # Live Firestore — use ID prefix range query
        col_ref = self._client.collection(col)
        results = []
        start = f"{author_id}__"
        end = f"{author_id}_" + "\uffff"
        for snap in col_ref.where("__name__", ">=", col_ref.document(start)).where(
            "__name__", "<", col_ref.document(end)
        ).stream():
            try:
                results.append(DevHabitDocument(**snap.to_dict()))
            except Exception:
                pass
        return results

    def get_all_habits(self, repo_id: str) -> List[DevHabitDocument]:
        """Returns all dev_habits for a repo."""
        col = self._collection_path(repo_id, "dev_habits")
        raw_docs = self._list_docs(col)
        results = []
        for raw in raw_docs:
            try:
                results.append(DevHabitDocument(**raw))
            except Exception:
                pass
        return results

    def count_habits(self, repo_id: str) -> int:
        return self._count_docs(self._collection_path(repo_id, "dev_habits"))

    # ------------------------------------------------------------------
    # Audit Log CRUD
    # ------------------------------------------------------------------

    def add_audit_log(self, repo_id: str, log_entry: AuditLogDocument) -> str:
        """Writes a new audit log entry.  Returns the generated doc ID."""
        col = self._collection_path(repo_id, "audit_log")
        doc_id = f"audit-{uuid.uuid4().hex[:12]}"
        data = log_entry.model_dump(mode="json")
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = v.isoformat()
        self._set_doc(col, doc_id, data)
        logger.info("Added audit log %s to repo %s: %s", doc_id, repo_id, log_entry.action_taken[:60])
        return doc_id

    def get_audit_logs(self, repo_id: str, limit: int = 100) -> List[AuditLogDocument]:
        col = self._collection_path(repo_id, "audit_log")
        raw_docs = self._list_docs(col, limit=limit)
        results = []
        for raw in raw_docs:
            try:
                results.append(AuditLogDocument(**raw))
            except Exception:
                pass
        return results

    def count_audit_logs(self, repo_id: str) -> int:
        return self._count_docs(self._collection_path(repo_id, "audit_log"))

    # ------------------------------------------------------------------
    # Memory Brief (compacted summary)
    # ------------------------------------------------------------------

    def save_memory_brief(self, repo_id: str, brief: MemoryBrief):
        """Saves the compacted memory brief (always overwrites 'latest')."""
        col = self._collection_path(repo_id, "memory_briefs")
        data = brief.model_dump(mode="json")
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = v.isoformat()
        self._set_doc(col, "latest", data)
        logger.info(
            "Saved memory brief for repo %s (%d decisions, %d habits summarised)",
            repo_id, brief.source_decision_count, brief.source_habit_count,
        )

    def get_memory_brief(self, repo_id: str) -> Optional[MemoryBrief]:
        """Loads the latest compacted memory brief for a repo."""
        col = self._collection_path(repo_id, "memory_briefs")
        raw = self._get_doc(col, "latest")
        if raw:
            try:
                return MemoryBrief(**raw)
            except Exception as exc:
                logger.warning("Failed to parse memory brief for repo %s: %s", repo_id, exc)
        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clear_mock_store(self):
        """Wipes all in-memory mock data (test helper)."""
        self._mock_store.clear()

    @property
    def is_mock(self) -> bool:
        return self._use_mock


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_firestore_instance: Optional[FirestoreMemoryBank] = None


def get_firestore_memory_bank(settings: Optional[Settings] = None) -> FirestoreMemoryBank:
    """Returns or creates the singleton FirestoreMemoryBank."""
    global _firestore_instance
    if _firestore_instance is None:
        _firestore_instance = FirestoreMemoryBank(settings=settings)
    return _firestore_instance
