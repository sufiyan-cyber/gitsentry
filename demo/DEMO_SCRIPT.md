# GitSentry: Official 4-Minute Demo Video Script
### All Things Agentic Hackathon — Collaborative Partner Track

---

## ⏱️ Video Structure Overview (4:00 Total)

| Timestamp | Phase | Visual Cue | Key Talking Points |
|---|---|---|---|
| **0:00 – 0:30** | Problem Statement | Architecture diagram & CodeRabbit comparison | Why stateless scanners fail: comment pollution, no memory, zero gating. |
| **0:30 – 0:45** | Value Proposition | GitSentry live UI overview | The 3 claims: Cross-PR Memory, Autonomous Remediation, Developer Adaptation. |
| **0:45 – 1:45** | **Beat 1 (PR #1)** | Live PR on GitHub | Staging unauthenticated `/health` -> Socratic pushback -> Accepted override recorded in Firestore. |
| **1:45 – 2:45** | **Beat 2 (PR #2)** | Live PR on GitHub + Auto-Fix PR | Production `/health` -> Memory citation of PR #1 -> Auto-opened remediation PR adding JWT auth. |
| **2:45 – 3:45** | **Beat 3 (PR #3)** | Live PR on GitHub + Habit Citation | Raw SQL query -> GitSentry detects 2nd occurrence for this author -> Cites prior PR. |
| **3:45 – 4:00** | Cloud Run & Logs | Google Cloud Console / Cloud Run Logs | Real GCP infrastructure: Pub/Sub ingestion, Secret Manager, Gemini 3.7 Flash request logs. |

---

## 🎙️ Verbatim Voiceover Script

### [0:00 – 0:30] The Problem
> *"Every developer has seen AI PR reviewers that dump 40 comments on a pull request, forget everything the second you click refresh, and can't actually fix anything. If your team accepted a temporary security exemption last week on staging, a stateless scanner will keep flagging it forever. And when a real vulnerability appears, all it does is leave advice. In production security, advice doesn't prevent breaches — gates and fixes do.*
>
> *Meet **GitSentry**: a stateful, collaborative AI security co-pilot for GitHub built on Gemini 3.7 Flash and Google Cloud."*

---

### [0:30 – 0:45] The 3 Core Proof Points
> *"In this 4-minute demo, we're going to prove three things live:*
> 1. *It remembers architectural decisions across pull requests.*
> 2. *It acts autonomously by opening real remediation PRs and gating merges.*
> 3. *It adapts to each specific developer's habits rather than just repo-level rules."*

---

### [0:45 – 1:45] Beat 1: PR #1 — Socratic Dialogue & Exemption Memory
*(Screen shows developer Alice opening PR #1 adding an unauthenticated `/health` endpoint)*

> *"Here, Alice pushes a new unauthenticated `/health` check for our staging environment. GitSentry's webhook receiver ingests the event in under 50 milliseconds via Google Cloud Pub/Sub. Gemini 3.7 Flash runs a deep audit, flags Broken Access Control, and sets our `gitsentry/security` commit status to FAILURE — blocking the merge.*
>
> *Watch what happens when Alice comments: '@gitsentry please override this, it's fine.'*
>
> *GitSentry doesn't blindly obey. It pushes back Socratically: 'Could you clarify the scope, compensating controls, and duration?'*
>
> *Now Alice replies with the full context: 'This is strictly for internal VPC synthetic monitoring probes in staging.'*
>
> *GitSentry evaluates the justification, accepts it, records the decision to our Firestore Memory Bank, and automatically clears the commit status to SUCCESS."*

---

### [1:45 – 2:45] Beat 2: PR #2 — Cross-PR Memory & Autonomous Remediation PR
*(Screen shows PR #2 where `/health` is now being exposed in production)*

> *"A few days later, Alice opens PR #2, exposing the same `/health` route pattern in a production configuration.*
>
> *A stateless bot would treat this as a generic finding. But GitSentry queries Firestore, reads the compacted architecture brief, and explicitly calls out the inconsistency:*
> *'This violates the approved decision from PR #1, which was strictly limited to staging VPC probes.'*
>
> *And notice: GitSentry doesn't just leave a comment. Because its confidence is 96% on a single file, it autonomously creates a new branch `gitsentry/fix-jwt-auth`, commits the JWT verification middleware, and opens a real remediation PR linked directly in the discussion.*
>
> *The merge remains blocked until the human engineer reviews and merges the fix. GitSentry never auto-merges code — human authority remains final."*

---

### [2:45 – 3:45] Beat 3: PR #3 — Adapting to the Specific Developer
*(Screen shows PR #3 where Alice submits a raw SQL query string)*

> *"In PR #3, Alice submits a user lookup query using raw SQL string concatenation.*
>
> *GitSentry checks the `dev_habits` collection specifically for `@dev-alice`. It notices this is the second time this exact pattern has appeared in her PRs.*
>
> *Look at the comment:*
> *'🔁 Recurring pattern — this is the 2nd time this pattern has appeared in your PRs (previously seen in PR #0).'*
>
> *It then offers an automated remediation patch with parameterized statements. This is the definition of the Collaborative Partner track: an assistant that learns your habits and actively coaches you across your engineering journey."*

---

### [3:45 – 4:00] GCP Architecture & Closing
*(Screen cuts to Google Cloud Console: Cloud Run services, Pub/Sub topic `pr-events`, and Vertex AI logs)*

> *"Under the hood, GitSentry runs decoupled on Google Cloud Run, backed by Google Secret Manager, Cloud Pub/Sub, and Firestore Memory compaction.*
>
> *GitSentry: Not just a comment bot — a stateful, collaborative security partner. Thank you!"*
