export interface PullRequestScenario {
  id: string;
  prNumber: number;
  title: string;
  author: string;
  repo: string;
  branch: string;
  category: "injection" | "architecture_override" | "cve_dependency" | "auth_bypass";
  description: string;
  riskTier: "HIGH" | "MEDIUM" | "SAFE";
  geminiTriage: {
    lowThinkingSummary: string;
    highThinkingAnalysis: string;
    thinkingLevelUsed: "LOW" | "HIGH";
    latencyMs: number;
  };
  memoryMatch: {
    decisionHit?: {
      id: string;
      description: string;
      approvedBy: string;
      prReference: string;
      status: "active" | "superseded";
    };
    habitHit?: {
      pattern: string;
      occurrencesCount: number;
      author: string;
    };
  };
  remediationPR: {
    title: string;
    branch: string;
    targetBranch: string;
    diffSnippet: string;
    status: "ready" | "applied" | "merged";
  };
  commitGateStatus: "failure" | "success" | "pending";
}

export interface FirestoreDecision {
  id: string;
  repo: string;
  description: string;
  approvedBy: string;
  prReference: string;
  createdAt: string;
  status: "active" | "superseded";
}

export interface FirestoreHabit {
  authorId: string;
  pattern: string;
  occurrences: string[];
  firstSeen: string;
  lastSeen: string;
  riskLevel: "HIGH" | "MEDIUM" | "LOW";
}

export const SAMPLE_PRS: PullRequestScenario[] = [
  {
    id: "pr-42",
    prNumber: 42,
    title: "feat(auth): add raw query lookup for legacy user migration",
    author: "dev_alex",
    repo: "gitsentry-core/identity-service",
    branch: "feature/legacy-users",
    category: "injection",
    riskTier: "HIGH",
    description: "Introduces dynamic SQL string interpolation inside the credential lookup endpoint.",
    geminiTriage: {
      lowThinkingSummary: "Risk Signal Detected: Unparameterized database query identified in user authentication flow.",
      highThinkingAnalysis: "DEEP THREAT AUDIT (Gemini 3.7 Flash):\n- Identified SQL Injection vector in `find_user_by_email()` using f-strings with unsanitized `email` input.\n- Attacker can bypass authentication via `' OR 1=1 --`.\n- Memory Bank Habit Match: Author `dev_alex` has 3 past instances of string concatenation in database queries.\n- Gate Action: FAILED commit status `gitsentry/security`.",
      thinkingLevelUsed: "HIGH",
      latencyMs: 1140,
    },
    memoryMatch: {
      habitHit: {
        pattern: "raw SQL string concatenation instead of parameterized queries",
        occurrencesCount: 3,
        author: "dev_alex",
      },
    },
    remediationPR: {
      title: "fix(security): parameterize SQL query in identity-service [#42]",
      branch: "gitsentry/fix-pr-42-sql-injection",
      targetBranch: "feature/legacy-users",
      diffSnippet: `--- a/services/auth/db.py\n+++ b/services/auth/db.py\n@@ -14,3 +14,3 @@\n- query = f"SELECT * FROM users WHERE email = '{email}'"\n- cursor.execute(query)\n+ query = "SELECT * FROM users WHERE email = %s"\n+ cursor.execute(query, (email,))`,
      status: "ready",
    },
    commitGateStatus: "failure",
  },
  {
    id: "pr-43",
    prNumber: 43,
    title: "chore(infra): allow unauthenticated probe on /health endpoint in staging",
    author: "dev_sarah",
    repo: "gitsentry-core/gateway-proxy",
    branch: "infra/staging-health-probe",
    category: "architecture_override",
    riskTier: "SAFE",
    description: "Bypasses JWT middleware for `/health` route on staging clusters.",
    geminiTriage: {
      lowThinkingSummary: "Triage Alert: Unauthenticated route change detected. Querying Firestore Memory Bank...",
      highThinkingAnalysis: "STATEFUL RECALL (Gemini 3.7 Flash):\n- Matched active architectural decision `DEC-89` ('Staging env allows unauthenticated /health route' approved by SecOps Lead @marcus in PR #19).\n- Change strictly conforms to documented policy. No elevation of privilege for production target.\n- Gate Action: SUCCESS commit status `gitsentry/security`.",
      thinkingLevelUsed: "HIGH",
      latencyMs: 820,
    },
    memoryMatch: {
      decisionHit: {
        id: "DEC-89",
        description: "Staging env allows unauthenticated /health route for internal synthetic monitors",
        approvedBy: "marcus (SecOps Lead)",
        prReference: "PR #19",
        status: "active",
      },
    },
    remediationPR: {
      title: "docs(compliance): reference DEC-89 in gateway-proxy config",
      branch: "gitsentry/docs-dec-89-ref",
      targetBranch: "infra/staging-health-probe",
      diffSnippet: `--- a/config/staging.yaml\n+++ b/config/staging.yaml\n@@ -8,2 +8,3 @@\n bypass_auth_routes:\n+  # Conforms to Decision DEC-89 approved in PR #19\n   - /health`,
      status: "applied",
    },
    commitGateStatus: "success",
  },
  {
    id: "pr-44",
    prNumber: 44,
    title: "bump(deps): upgrade cryptography and urllib3 across services",
    author: "dependabot[bot]",
    repo: "gitsentry-core/worker-service",
    branch: "deps/urllib3-update",
    category: "cve_dependency",
    riskTier: "HIGH",
    description: "Updates dependencies; introduces transitive dependency vulnerability indexed in OSV.dev.",
    geminiTriage: {
      lowThinkingSummary: "Dependency Manifest Diff detected. Querying OSV.dev Vulnerability Database...",
      highThinkingAnalysis: "CVE & OSV.DEV AUDIT:\n- Found GHSA-w787-c79q-63p3 (CVE-2023-45803) in transitive package `urllib3<2.0.7`.\n- Criticality: High (CVSS 7.5) — Request Header Strip bypass during cross-origin redirect.\n- Gate Action: BLOCKED merge via `gitsentry/security`.\n- Remediation: Autonomously generated patch upgrading constraint to `urllib3>=2.0.7`.",
      thinkingLevelUsed: "HIGH",
      latencyMs: 960,
    },
    memoryMatch: {},
    remediationPR: {
      title: "fix(deps): pin urllib3>=2.0.7 to remediate CVE-2023-45803 [#44]",
      branch: "gitsentry/fix-cve-2023-45803",
      targetBranch: "deps/urllib3-update",
      diffSnippet: `--- a/requirements.txt\n+++ b/requirements.txt\n@@ -5,1 +5,1 @@\n-urllib3==2.0.4\n+urllib3>=2.0.7  # Remediates GHSA-w787-c79q-63p3`,
      status: "ready",
    },
    commitGateStatus: "failure",
  },
];

export const FIRESTORE_DECISIONS: FirestoreDecision[] = [
  {
    id: "DEC-89",
    repo: "gitsentry-core/gateway-proxy",
    description: "Staging env allows unauthenticated /health route for synthetic uptime monitoring",
    approvedBy: "marcus (SecOps Lead)",
    prReference: "PR #19",
    createdAt: "2026-02-14",
    status: "active",
  },
  {
    id: "DEC-94",
    repo: "gitsentry-core/identity-service",
    description: "All SQL transactions must execute through SQLAlchemy ORM or parameterized prepared statements",
    approvedBy: "elena (Principal Architect)",
    prReference: "PR #27",
    createdAt: "2026-04-02",
    status: "active",
  },
  {
    id: "DEC-102",
    repo: "gitsentry-core/worker-service",
    description: "Secret Manager runtime mounting required; zero env vars for raw private keys in container layers",
    approvedBy: "david (DevOps Lead)",
    prReference: "PR #33",
    createdAt: "2026-06-19",
    status: "active",
  },
];

export const FIRESTORE_HABITS: FirestoreHabit[] = [
  {
    authorId: "dev_alex",
    pattern: "raw SQL string concatenation instead of parameterized queries",
    occurrences: ["PR #12", "PR #31", "PR #42"],
    firstSeen: "2026-01-10",
    lastSeen: "2026-08-28",
    riskLevel: "HIGH",
  },
  {
    authorId: "dev_chen",
    pattern: "missing exponential backoff on third-party HTTP retry loops",
    occurrences: ["PR #08", "PR #22"],
    firstSeen: "2026-03-05",
    lastSeen: "2026-07-11",
    riskLevel: "MEDIUM",
  },
  {
    authorId: "dev_sarah",
    pattern: "wildcard CORS headers (`Access-Control-Allow-Origin: *`) in staging configs",
    occurrences: ["PR #15"],
    firstSeen: "2026-05-18",
    lastSeen: "2026-05-18",
    riskLevel: "MEDIUM",
  },
];

export const FAQ_ITEMS = [
  {
    id: "faq-1",
    question: "How does GitSentry leverage Gemini 3.7 Flash dual-tier thinking?",
    answer: "GitSentry uses a cost- and latency-optimized two-tier pipeline. Every GitHub webhook event triggers a rapid triage pass with thinking_level=LOW (<200ms) to check for security-relevant diffs. When potential vulnerabilities or architectural overrides are detected, GitSentry escalates to a deep audit pass with thinking_level=HIGH, combining AST analysis, OSV.dev CVE database lookups, and stateful memory queries.",
  },
  {
    id: "faq-2",
    question: "What makes GitSentry 'stateful' compared to traditional scanners?",
    answer: "Stateless security scanners produce repetitive false positives because they forget human context. GitSentry persists architectural decisions, security exceptions, and developer habits across pull requests in Google Cloud Firestore. When a developer changes an endpoint, GitSentry checks historical decisions (e.g. 'Staging unauthenticated /health route approved in PR #19') before flagging.",
  },
  {
    id: "faq-3",
    question: "How does autonomous remediation and merge commit gating work?",
    answer: "When a vulnerability is verified, GitSentry immediately sets the GitHub commit status check `gitsentry/security` to 'failure', blocking the merge. Concurrently, GitSentry creates a new remediation branch containing a precision diff (e.g., parameterizing SQL or pinning a secure dependency) and opens a companion pull request.",
  },
  {
    id: "faq-4",
    question: "How does decoupled Cloud Run + Pub/Sub ingestion prevent dropped events?",
    answer: "GitHub webhooks require an HTTP 200 response within 10 seconds. Deep AI audits and database queries can take longer under peak load. The lightweight Webhook Receiver validates HMAC-SHA256 signatures, publishes the normalized payload to Google Cloud Pub/Sub, and replies in milliseconds. The Worker Service pulls from Pub/Sub with guaranteed delivery.",
  },
  {
    id: "faq-5",
    question: "How are secrets and API credentials managed in production?",
    answer: "Zero secrets are committed to git or baked into Docker container layers. GitHub App private keys, Webhook HMAC secrets, and Gemini API keys are mounted dynamically at runtime via Google Cloud Secret Manager with TTL in-memory caching and constant-time verification.",
  },
];
