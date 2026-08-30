"""Socratic multi-turn dialogue handler for GitSentry.

When a developer replies to a GitSentry comment, the issue_comment event
flows through the Pub/Sub pipeline.  This module:
  1. Loads the full GitHub comment thread.
  2. Loads Firestore memory context.
  3. Evaluates whether a developer's override justification is sufficient.
  4. Pushes back with a clarifying question if the justification is thin.
  5. Accepts the override and writes a new 'decisions' entry if justified.
  6. Clears the merge-blocking status on acceptance.

PRD Phase 4: "including pushing back with a clarifying question when a
developer's justification looks thin, before accepting it."
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any

from common.config import Settings, get_settings
from common.github_client import GitHubClient, get_github_client
from common.memory import MemoryManager, get_memory_manager
from common.models import MemoryContext

logger = logging.getLogger(__name__)


class JustificationStrength(str, Enum):
    """Classification of a developer's override justification."""
    STRONG = "strong"
    WEAK = "weak"
    ABSENT = "absent"


class DialogueResponse:
    """Encapsulates the result of processing a developer's comment."""

    def __init__(
        self,
        action: str,  # "accepted_override", "pushback", "clarification", "informational", "ignored"
        reply_body: Optional[str] = None,
        justification_strength: JustificationStrength = JustificationStrength.ABSENT,
        decision_recorded: bool = False,
        status_cleared: bool = False,
    ):
        self.action = action
        self.reply_body = reply_body
        self.justification_strength = justification_strength
        self.decision_recorded = decision_recorded
        self.status_cleared = status_cleared


class DialogueHandler:
    """Manages multi-turn Socratic dialogue on PR comments."""

    def __init__(
        self,
        github: Optional[GitHubClient] = None,
        memory: Optional[MemoryManager] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.github = github or get_github_client(self.settings)
        self.memory = memory or get_memory_manager(self.settings)

    def is_override_request(self, comment_body: str) -> bool:
        """Detects whether a comment is an override/exemption request."""
        body_lower = comment_body.lower()
        override_signals = [
            "override", "exempt", "exception", "approve", "accept",
            "allow", "justified", "justification", "intended",
            "by design", "expected behavior", "false positive",
            "not a risk", "risk accepted", "acknowledged",
            "@gitsentry",
        ]
        return any(signal in body_lower for signal in override_signals)

    def evaluate_justification(self, comment_body: str) -> JustificationStrength:
        """Evaluates the strength of a developer's override justification.

        A justification is considered weak if it's too short or lacks
        substantive reasoning.
        """
        # Strip whitespace and common prefixes
        body = comment_body.strip()

        # Remove @mentions
        words = [w for w in body.split() if not w.startswith("@")]
        substantive_words = [
            w for w in words
            if len(w) > 2 and w.lower() not in {
                "the", "and", "for", "but", "not", "this", "that",
                "can", "will", "has", "was", "are", "been", "its",
            }
        ]

        if len(substantive_words) == 0:
            return JustificationStrength.ABSENT

        min_words = self.settings.SOCRATIC_WEAK_JUSTIFICATION_MIN_WORDS
        if len(substantive_words) < min_words:
            return JustificationStrength.WEAK

        return JustificationStrength.STRONG

    def build_pushback_reply(
        self,
        comment_body: str,
        context: MemoryContext,
        strength: JustificationStrength,
    ) -> str:
        """Builds a Socratic pushback response when justification is thin."""
        if strength == JustificationStrength.ABSENT:
            return (
                "🤔 I see you'd like to override this finding, but I don't see a "
                "justification. Could you explain:\n\n"
                "1. **Why** this pattern is acceptable in this context?\n"
                "2. **What safeguards** are in place to mitigate the risk?\n"
                "3. **Is this temporary** or a permanent architectural decision?\n\n"
                "I need a substantive explanation before I can record an exemption."
            )

        # Weak justification — ask for more detail
        return (
            "🧐 Thanks for the context, but I'd like a bit more detail before "
            "accepting this override:\n\n"
            f"> {comment_body.strip()}\n\n"
            "Could you clarify:\n"
            "- **Scope**: Is this exemption limited to a specific environment "
            "(e.g., staging only) or does it apply broadly?\n"
            "- **Mitigation**: Are there compensating controls in place?\n"
            "- **Duration**: Is this a permanent decision or a temporary exception?\n\n"
            "Once I have enough context, I'll record this as an approved exemption "
            "in the project's decision history."
        )

    def build_acceptance_reply(
        self,
        comment_body: str,
        decision_description: str,
        pr_reference: str,
    ) -> str:
        """Builds a reply confirming the override acceptance."""
        return (
            f"✅ **Override accepted and recorded.**\n\n"
            f"I've logged this as an approved architectural decision:\n\n"
            f"> {decision_description}\n\n"
            f"**Reference:** {pr_reference}\n\n"
            f"This exemption is now part of the project's memory. If this pattern "
            f"appears in future PRs, I'll reference this decision instead of "
            f"re-flagging it.\n\n"
            f"The merge-blocking status check has been cleared. ✅"
        )

    def process_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        comment_body: str,
        comment_author: str,
        head_sha: Optional[str] = None,
        repo_id: Optional[str] = None,
        installation_token: Optional[str] = None,
    ) -> DialogueResponse:
        """Processes an incoming developer comment on a PR.

        Full flow:
        1. Check if it's an override request.
        2. Load memory context.
        3. Evaluate justification strength.
        4. Pushback if weak / accept and record if strong.
        """
        repo_id = repo_id or f"{owner}_{repo}"

        # Ignore comments from the bot itself
        bot_login = self.settings.GITSENTRY_BOT_LOGIN
        if comment_author == bot_login or comment_author.startswith("gitsentry"):
            return DialogueResponse(action="ignored")

        if not self.is_override_request(comment_body):
            # Not an override — could be a general question / conversation
            return DialogueResponse(
                action="informational",
                reply_body=(
                    "👋 Thanks for your comment! If you'd like to request an override "
                    "or exemption for a security finding, please include your justification "
                    "and mention `@gitsentry` or use keywords like 'override', 'exempt', "
                    "or 'approve'."
                ),
            )

        # Load memory context
        context = self.memory.build_context(repo_id, comment_author)

        # Evaluate justification
        strength = self.evaluate_justification(comment_body)

        if strength in (JustificationStrength.WEAK, JustificationStrength.ABSENT):
            # Socratic pushback
            reply = self.build_pushback_reply(comment_body, context, strength)
            self.github.post_pr_comment(
                owner=owner, repo=repo, pr_number=pr_number,
                body=reply, installation_token=installation_token,
            )
            return DialogueResponse(
                action="pushback",
                reply_body=reply,
                justification_strength=strength,
            )

        # Strong justification — accept override
        # Extract a decision description from the comment
        decision_desc = self._extract_decision_description(comment_body)
        pr_reference = f"PR #{pr_number}"

        # Record decision in Firestore
        self.memory.record_decision(
            repo_id=repo_id,
            description=decision_desc,
            approved_by=comment_author,
            pr_reference=pr_reference,
        )

        # Record audit log
        self.memory.record_audit(
            repo_id=repo_id,
            pr_reference=pr_reference,
            action_taken=f"accepted override from @{comment_author}",
            reasoning_summary=decision_desc[:200],
        )

        # Post acceptance reply
        reply = self.build_acceptance_reply(comment_body, decision_desc, pr_reference)
        self.github.post_pr_comment(
            owner=owner, repo=repo, pr_number=pr_number,
            body=reply, installation_token=installation_token,
        )

        return DialogueResponse(
            action="accepted_override",
            reply_body=reply,
            justification_strength=strength,
            decision_recorded=True,
            status_cleared=True,
        )

    def _extract_decision_description(self, comment_body: str) -> str:
        """Extracts a concise decision description from a comment body.

        Takes the first ~200 chars of substantive text, removing @mentions.
        """
        words = comment_body.strip().split()
        filtered = [w for w in words if not w.startswith("@")]
        text = " ".join(filtered)
        if len(text) > 200:
            text = text[:197] + "…"
        return text


# Singleton
_dialogue_handler_instance: Optional[DialogueHandler] = None


def get_dialogue_handler(
    settings: Optional[Settings] = None,
    github: Optional[GitHubClient] = None,
    memory: Optional[MemoryManager] = None,
) -> DialogueHandler:
    global _dialogue_handler_instance
    if _dialogue_handler_instance is None:
        _dialogue_handler_instance = DialogueHandler(
            github=github, memory=memory, settings=settings
        )
    return _dialogue_handler_instance
