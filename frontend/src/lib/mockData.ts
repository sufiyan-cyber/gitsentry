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
    id: "pr-1",
    prNumber: 1,
    title: "feat(staging): add unauthenticated health probe",
    author: "sufiyantesting789",
    repo: "sufiyantesting789/production-web",
    branch: "feature/staging-health",
    category: "architecture_override",
    riskTier: "SAFE",
    description: "Adds an unauthenticated `/health` probe route in staging environment with Socratic exemption.",
    geminiTriage: {
      lowThinkingSummary: "Triage Alert (<180ms): Unauthenticated route detected. Initiating Socratic verification...",
      highThinkingAnalysis: "SOCRATIC EXEMPTION VALIDATION (Gemini 3.7 Flash):\n- Flagged Broken Access Control on `/health`.\n- Developer @sufiyantesting789 requested override with VPC isolation justification.\n- Socratic Evaluator rated justification: STRONG.\n- Created active decision `DEC-89` in Google Firestore Memory Bank.\n- Gate Action: SUCCESS commit status `gitsentry/security` (Merge Unblocked).",
      thinkingLevelUsed: "HIGH",
      latencyMs: 740,
    },
    memoryMatch: {
      decisionHit: {
        id: "DEC-89",
        description: "Staging env allows unauthenticated /health route for internal VPC synthetic uptime monitors",
        approvedBy: "sufiyantesting789 (SecOps Lead)",
        prReference: "PR #1",
        status: "active",
      },
    },
    remediationPR: {
      title: "docs(compliance): record DEC-89 VPC exemption in production-web",
      branch: "gitsentry/docs-dec-89",
      targetBranch: "feature/staging-health",
      diffSnippet: `--- a/src/routes/health.py\n+++ b/src/routes/health.py\n@@ -5,3 +5,4 @@\n+# [GitSentry DEC-89]: Allowed unauthenticated for VPC synthetic probe only\n @app.get("/health")\n def staging_health():\n     return {"status": "healthy", "env": "staging"}`,
      status: "ready",
    },
    commitGateStatus: "success",
  },
  {
    id: "pr-2",
    prNumber: 2,
    title: "feat(prod): expose health probe on production",
    author: "sufiyantesting789",
    repo: "sufiyantesting789/production-web",
    branch: "feature/prod-health",
    category: "auth_bypass",
    riskTier: "HIGH",
    description: "Attempts to deploy unauthenticated health route to production cluster, violating PR #1 staging scope.",
    geminiTriage: {
      lowThinkingSummary: "Risk Signal Detected: Unauthenticated endpoint detected in production service route.",
      highThinkingAnalysis: "CROSS-PR MEMORY RECALL (Gemini 3.7 Flash):\n- Queried Firestore Collection `projects/production-web/decisions`.\n- Found Decision `DEC-89` from PR #1 strictly limited to staging VPC synthetic probes.\n- Production exposure violates security boundary. Blocked merge.\n- Autonomously synthesized JWT authentication patch and opened remediation branch `gitsentry/fix-jwt-auth`.",
      thinkingLevelUsed: "HIGH",
      latencyMs: 1220,
    },
    memoryMatch: {
      decisionHit: {
        id: "DEC-89",
        description: "Staging env allows unauthenticated /health route for internal VPC synthetic monitors ONLY",
        approvedBy: "sufiyantesting789 (SecOps Lead)",
        prReference: "PR #1",
        status: "active",
      },
    },
    remediationPR: {
      title: "fix(security): add JWT authentication middleware to production health probe [#2]",
      branch: "gitsentry/fix-jwt-auth",
      targetBranch: "feature/prod-health",
      diffSnippet: `--- a/src/routes/health.py\n+++ b/src/routes/health.py\n@@ -1,4 +1,5 @@\n from fastapi import FastAPI, Depends\n+from auth import verify_jwt_token\n \n app = FastAPI()\n \n-@app.get("/health")\n-def prod_health():\n+@app.get("/health", dependencies=[Depends(verify_jwt_token)])\n+def prod_health():\n     return {"status": "healthy", "env": "production"}`,
      status: "ready",
    },
    commitGateStatus: "failure",
  },
  {
    id: "pr-3",
    prNumber: 3,
    title: "feat(auth): lookup user by email with raw SQL query",
    author: "sufiyantesting789",
    repo: "sufiyantesting789/production-web",
    branch: "feature/user-lookup",
    category: "injection",
    riskTier: "HIGH",
    description: "Introduces dynamic SQL string interpolation in user lookup query.",
    geminiTriage: {
      lowThinkingSummary: "Risk Signal Detected (<190ms): Unparameterized raw SQL string concatenation found.",
      highThinkingAnalysis: "DEVELOPER HABIT PROFILING (Gemini 3.7 Flash):\n- Identified SQL Injection vector: `f\"SELECT * FROM users WHERE email = '{email}'\"`.\n- Firestore Habit Match: Author @sufiyantesting789 has 3 past instances of string concatenation.\n- Flagged as recurring pattern with tailored coaching on parameterized queries.\n- Gate Action: FAILED commit status `gitsentry/security`.",
      thinkingLevelUsed: "HIGH",
      latencyMs: 1080,
    },
    memoryMatch: {
      habitHit: {
        pattern: "raw SQL string concatenation instead of parameterized queries",
        occurrencesCount: 3,
        author: "sufiyantesting789",
      },
    },
    remediationPR: {
      title: "fix(security): parameterize SQL query in user lookup [#3]",
      branch: "gitsentry/fix-parameterized-sql",
      targetBranch: "feature/user-lookup",
      diffSnippet: `--- a/src/db/users.py\n+++ b/src/db/users.py\n@@ -2,3 +2,3 @@\n def get_user_by_email(email: str):\n-    query = f"SELECT * FROM users WHERE email = '{email}'"\n-    return db.execute(query)\n+    query = "SELECT * FROM users WHERE email = %s"\n+    return db.execute(query, (email,))`,
      status: "ready",
    },
    commitGateStatus: "failure",
  },
];

export const INITIAL_DECISIONS: FirestoreDecision[] = [
  {
    id: "DEC-89",
    repo: "sufiyantesting789/production-web",
    description: "Staging env allows unauthenticated /health route for internal VPC synthetic uptime monitors",
    approvedBy: "sufiyantesting789 (SecOps Lead)",
    prReference: "PR #1",
    createdAt: "2026-08-30T10:15:00Z",
    status: "active",
  },
  {
    id: "DEC-88",
    repo: "sufiyantesting789/production-web",
    description: "Require TLS 1.3 encryption and mTLS for all inter-service mesh communications",
    approvedBy: "sufiyantesting789 (SecOps Lead)",
    prReference: "PR #0",
    createdAt: "2026-08-28T14:30:00Z",
    status: "active",
  },
];

export const FIRESTORE_DECISIONS = INITIAL_DECISIONS;

export const INITIAL_HABITS: FirestoreHabit[] = [
  {
    authorId: "sufiyantesting789",
    pattern: "raw SQL string concatenation instead of parameterized queries",
    occurrences: ["PR #3", "PR #0"],
    firstSeen: "2026-08-28T11:00:00Z",
    lastSeen: "2026-08-30T10:45:00Z",
    riskLevel: "HIGH",
  },
];

export const FIRESTORE_HABITS = INITIAL_HABITS;

export const FAQ_ITEMS = [
  {
    id: "faq-1",
    question: "How does GitSentry remember architectural security decisions across PRs?",
    answer:
      "GitSentry automatically indexes approved security exemptions, compensating controls, and risk acceptances in a Google Cloud Firestore Memory Bank. When new PRs are submitted, GitSentry uses Gemini 3.7 Flash with high-thinking mode to perform stateful recall, checking whether the new code respects prior constraints or attempts to expand the exemption scope without authorization.",
  },
  {
    id: "faq-2",
    question: "What is Socratic Dialogue and how does it prevent security fatigue?",
    answer:
      "Unlike traditional noisy security bots that post rigid pass/fail blockers, GitSentry engages in context-aware Socratic dialogue. If a developer requests an override or provides compensating architecture, GitSentry evaluates the justification, asks probing verification questions, and upon consensus, automatically unblocks the PR and commits the decision to persistent memory.",
  },
  {
    id: "faq-3",
    question: "How does GitSentry generate autonomous remediation PRs?",
    answer:
      "When a critical vulnerability (such as an unauthenticated endpoint or SQL injection) is confirmed, GitSentry does not just point out the flaw. It uses Gemini 3.7 Flash to synthesize the exact patch diff, checks out a new branch (`gitsentry/fix-...`), and opens a fully formed, ready-to-merge Pull Request with test coverage.",
  },
  {
    id: "faq-4",
    question: "How does GitSentry track developer habits and provide tailored coaching?",
    answer:
      "GitSentry maintains privacy-preserving developer habit profiles in Firestore. If an engineer frequently writes dynamic string concatenations instead of parameterized database queries, GitSentry recognizes the recurring anti-pattern and shifts from generic alerts to personalized educational coaching.",
  },
];

