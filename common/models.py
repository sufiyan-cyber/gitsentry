"""Pydantic data models for GitHub webhook events, normalized Pub/Sub messages, and Firestore Memory Bank."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# GitHub Raw & Partial Models
# ---------------------------------------------------------------------------

class GitHubUser(BaseModel):
    login: str
    id: int
    type: str = "User"
    site_admin: bool = False
    html_url: Optional[str] = None


class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool = False
    owner: Optional[GitHubUser] = None
    default_branch: str = "main"
    html_url: Optional[str] = None


class GitHubGitRef(BaseModel):
    sha: str
    ref: str
    repo: Optional[GitHubRepository] = None


class GitHubPullRequest(BaseModel):
    number: int
    id: int
    title: str = ""
    body: Optional[str] = None
    state: str = "open"
    user: Optional[GitHubUser] = None
    head: Optional[GitHubGitRef] = None
    base: Optional[GitHubGitRef] = None
    diff_url: Optional[str] = None
    html_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def head_sha(self) -> Optional[str]:
        return self.head.sha if self.head else None

    @property
    def base_sha(self) -> Optional[str]:
        return self.base.sha if self.base else None

    @property
    def author_login(self) -> Optional[str]:
        return self.user.login if self.user else None


class GitHubIssue(BaseModel):
    number: int
    id: int
    title: str = ""
    body: Optional[str] = None
    user: Optional[GitHubUser] = None
    pull_request: Optional[Dict[str, Any]] = None  # Presence indicates it's a PR


class GitHubIssueComment(BaseModel):
    id: int
    body: str = ""
    user: Optional[GitHubUser] = None
    html_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GitHubInstallation(BaseModel):
    id: int
    node_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Normalized Pub/Sub Event (Contract for Phase 1 -> Phase 2 decoupled worker)
# ---------------------------------------------------------------------------

class EventType(str, Enum):
    PULL_REQUEST = "pull_request"
    ISSUE_COMMENT = "issue_comment"
    PING = "ping"
    UNSUPPORTED = "unsupported"


class NormalizedGitHubEvent(BaseModel):
    """Clean, standardized event payload sent across Pub/Sub topic 'pr-events'."""

    event_id: str = Field(description="Unique delivery ID from X-GitHub-Delivery header")
    event_type: EventType = Field(description="Type of GitHub event")
    action: str = Field(description="GitHub event action (e.g. 'opened', 'synchronize', 'created')")
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    installation_id: Optional[int] = Field(default=None, description="GitHub App installation ID")

    repository: GitHubRepository
    sender: GitHubUser

    # Pull Request context
    pull_request: Optional[GitHubPullRequest] = None
    issue_number: Optional[int] = None
    is_pull_request: bool = False

    # Issue comment context (if event_type == ISSUE_COMMENT)
    issue_comment: Optional[GitHubIssueComment] = None

    # Meta flags
    should_process: bool = True
    reason: Optional[str] = None

    def get_repo_id(self) -> str:
        """Returns normalized repo key for Firestore (e.g. 'owner_repo' or repo full_name)."""
        return self.repository.full_name.replace("/", "_")

    def get_author_login(self) -> str:
        """Returns author login of the PR or comment."""
        if self.pull_request and self.pull_request.user:
            return self.pull_request.user.login
        if self.issue_comment and self.issue_comment.user:
            return self.issue_comment.user.login
        return self.sender.login


# ---------------------------------------------------------------------------
# Gemini Structured Output Schemas (Phase 2)
# ---------------------------------------------------------------------------

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class SecurityFinding(BaseModel):
    """Structured security finding from Gemini 3.7 Flash high-thinking pass."""
    severity: SeverityLevel
    line_range: str = Field(description="e.g. '42-48' or '15'")
    owasp_category: str = Field(description="e.g. 'A01:2021-Broken Access Control'")
    explanation: str = Field(description="Clear explanation of the vulnerability and impact")
    suggested_fix: str = Field(description="Actionable code fix or remediation instruction")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    file_path: Optional[str] = Field(default=None, description="Affected file path")


class DeepAuditResult(BaseModel):
    findings: List[SecurityFinding] = Field(default_factory=list)
    summary: str = Field(description="Overall executive summary of audit findings")
    remediation_recommendation: Literal["BLOCK_MERGE", "OPEN_REMEDIATION_PR", "COMMENT_ONLY", "APPROVE"] = "APPROVE"


class TriageResult(BaseModel):
    """Result of Gemini 3.7 Flash low-thinking triage pass."""
    has_security_concerns: bool
    reason: str
    flagged_categories: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Firestore Memory Bank Schemas (PRD Section 4)
# ---------------------------------------------------------------------------

class DecisionStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class DecisionDocument(BaseModel):
    """Firestore: projects/{repo_id}/decisions/{decision_id}"""
    description: str
    approved_by: str
    pr_reference: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: DecisionStatus = DecisionStatus.ACTIVE


class DevHabitDocument(BaseModel):
    """Firestore: projects/{repo_id}/dev_habits/{author_id}"""
    pattern: str
    occurrences: List[str] = Field(default_factory=list, description="Array of PR references")
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLogDocument(BaseModel):
    """Firestore: projects/{repo_id}/audit_log/{event_id}"""
    pr_reference: str
    action_taken: str
    reasoning_summary: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Phase 3 — Memory Bank Context & Compaction Models
# ---------------------------------------------------------------------------

class MemoryBrief(BaseModel):
    """Compacted per-repo architecture memory brief stored in Firestore.
    
    Firestore path: projects/{repo_id}/memory_briefs/latest
    
    This is the condensed summary that actually gets injected into Gemini's context,
    NOT the full raw history. Keeps prompt size bounded as the repo grows.
    """
    repo_id: str
    decisions_summary: str = Field(
        default="",
        description="Condensed summary of all active architectural decisions and exemptions"
    )
    habits_summary: str = Field(
        default="",
        description="Condensed summary of recurring developer patterns across the repo"
    )
    total_decisions: int = 0
    total_habits: int = 0
    total_audits: int = 0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_decision_count: int = Field(
        default=0,
        description="Number of raw decision docs this brief was generated from"
    )
    source_habit_count: int = Field(
        default=0,
        description="Number of raw dev_habits docs this brief was generated from"
    )


class ExemptionMatch(BaseModel):
    """Result of matching a finding against an active decision/exemption."""
    matched: bool = False
    decision_id: Optional[str] = None
    description: str = ""
    pr_reference: str = ""
    approved_by: str = ""


class HabitMatch(BaseModel):
    """Result of matching a finding against a developer's recurring habits."""
    matched: bool = False
    pattern: str = ""
    occurrence_count: int = 0
    prior_prs: List[str] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class MemoryContext(BaseModel):
    """Full memory context assembled for injection into Gemini's system prompt.
    
    Built before each deep audit pass by combining:
    - The compacted MemoryBrief for the repo
    - Raw active decisions (for exemption matching)
    - Author-specific dev_habits (for habit counting)
    """
    repo_id: str
    author_id: str
    brief: Optional[MemoryBrief] = None
    active_decisions: List[DecisionDocument] = Field(default_factory=list)
    author_habits: List[DevHabitDocument] = Field(default_factory=list)
    
    def to_system_prompt_section(self) -> str:
        """Renders this memory context as a text block for Gemini's system prompt."""
        parts: List[str] = []
        
        parts.append(f"## Repository Memory Context ({self.repo_id})")
        parts.append("")
        
        # Compacted brief
        if self.brief:
            if self.brief.decisions_summary:
                parts.append("### Architectural Decisions & Exemptions")
                parts.append(self.brief.decisions_summary)
                parts.append("")
            if self.brief.habits_summary:
                parts.append("### Known Developer Patterns (repo-wide)")
                parts.append(self.brief.habits_summary)
                parts.append("")
        
        # Active exemptions for direct matching
        if self.active_decisions:
            parts.append("### Active Exemptions (do NOT re-flag these)")
            for d in self.active_decisions:
                parts.append(
                    f"- **{d.description}** — approved by {d.approved_by} "
                    f"in {d.pr_reference} (status: {d.status.value})"
                )
            parts.append("")
        
        # Author-specific habits
        if self.author_habits:
            parts.append(f"### Developer Habits for @{self.author_id}")
            for h in self.author_habits:
                count = len(h.occurrences)
                pr_list = ", ".join(h.occurrences[-5:])  # Show last 5 PRs
                parts.append(
                    f"- **{h.pattern}** — seen {count} time(s) in PRs: {pr_list}"
                )
            parts.append("")
        
        if not self.brief and not self.active_decisions and not self.author_habits:
            parts.append("No prior memory context available for this repository/author.")
            parts.append("")
        
        return "\n".join(parts)
    
    def find_exemption(self, finding_description: str) -> ExemptionMatch:
        """Checks if a finding description matches any active decision/exemption.
        
        Uses case-insensitive substring matching on the decision description.
        """
        finding_lower = finding_description.lower()
        for decision in self.active_decisions:
            if decision.status != DecisionStatus.ACTIVE:
                continue
            desc_lower = decision.description.lower()
            # Check for meaningful overlap: at least one significant phrase
            # Split into words and check for overlap
            finding_words = set(finding_lower.split())
            desc_words = set(desc_lower.split())
            # Remove common stop words
            stop_words = {"the", "a", "an", "is", "in", "on", "for", "of", "to", "and", "or", "this", "that"}
            finding_keywords = finding_words - stop_words
            desc_keywords = desc_words - stop_words
            overlap = finding_keywords & desc_keywords
            # If >= 40% keyword overlap or direct substring match
            if len(overlap) >= max(2, len(desc_keywords) * 0.4) or desc_lower in finding_lower or finding_lower in desc_lower:
                return ExemptionMatch(
                    matched=True,
                    decision_id=decision.pr_reference,  # Using PR ref as ID
                    description=decision.description,
                    pr_reference=decision.pr_reference,
                    approved_by=decision.approved_by,
                )
        return ExemptionMatch(matched=False)
    
    def find_habit_match(self, pattern_description: str) -> HabitMatch:
        """Checks if a finding matches a prior dev_habits entry for this author.
        
        Uses case-insensitive keyword matching on the habit pattern.
        """
        pattern_lower = pattern_description.lower()
        for habit in self.author_habits:
            habit_lower = habit.pattern.lower()
            pattern_words = set(pattern_lower.split())
            habit_words = set(habit_lower.split())
            stop_words = {"the", "a", "an", "is", "in", "on", "for", "of", "to", "and", "or", "this", "that"}
            pattern_keywords = pattern_words - stop_words
            habit_keywords = habit_words - stop_words
            overlap = pattern_keywords & habit_keywords
            if len(overlap) >= max(2, len(habit_keywords) * 0.4) or habit_lower in pattern_lower or pattern_lower in habit_lower:
                return HabitMatch(
                    matched=True,
                    pattern=habit.pattern,
                    occurrence_count=len(habit.occurrences),
                    prior_prs=habit.occurrences,
                    first_seen=habit.first_seen,
                    last_seen=habit.last_seen,
                )
        return HabitMatch(matched=False)
