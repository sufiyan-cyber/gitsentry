# GitSentry Worker Service (Phases 2–4)

This service runs as a decoupled Cloud Run service or Pub/Sub push/pull consumer. It processes normalized events from the `pr-events` topic.

## Pipeline Architecture
1. **Pub/Sub Trigger**: Ingests `NormalizedGitHubEvent`.
2. **GitHub API Client**: Fetches full PR diff using GitHub App installation access token.
3. **Triage Pass (Gemini 3.7 Flash, `thinking_level=LOW`)**:
   - Fast binary classifier for security relevance.
   - If clean, reports status and stops immediately (cost control).
4. **Deep Security Audit Pass (Gemini 3.7 Flash, `thinking_level=HIGH`)**:
   - OWASP Top 10 + AI-generated code vulnerabilities.
   - Injects Firestore Memory Bank (`decisions` + `dev_habits`).
   - Queries OSV.dev API tool for dependency CVEs.
   - Produces structured JSON output (`SecurityFinding`).
5. **Action Layer**:
   - Opens remediation PRs for high-confidence findings.
   - Sets GitHub commit status check (`gitsentry/security`).
   - Manages Socratic multi-turn dialogue on PR comments.
   - Updates Firestore memory bank.
