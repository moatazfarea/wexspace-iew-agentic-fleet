# Demo video script — target 3:45

Status: **Cloud proof is available; final video production and public upload remain open.** Record in English or add complete English subtitles. Use one continuous execution where practical. Do not show fake logs, secret values, personal browser data, or functionality that did not pass.

## 0:00–0:15 — Show the real result first

**Narration:**

“This is WEXSPACE AI running on Google Cloud Run: a governed three-agent engineering workflow using Google ADK and Gemini 3.7 Flash.”

**Screen:** Live `.run` URL, successful `/health`, then a two-second cut to the structured `/adk/live` result. No title-only opening.

## 0:15–0:35 — Problem and value

**Narration:**

“Industrial engineering work is more than producing an answer. Inputs must be complete, calculations reproducible, checks independent, decisions traceable, and consequential results released by an accountable human. WEXSPACE AI turns that workflow into a governed agent fleet.”

**Screen:** Title card, then the synthetic network JSON. Keep the word `SYNTHETIC` visible.

## 0:35–0:55 — Why a fleet, not a chatbot

**Narration:**

“A language model is not the numerical authority. The WEXSPACE Governing Agent controls context, policy, and routing. The IEW Engineering Specialist invokes deterministic equations. The WEXSPACE Verification and Evidence Specialist recomputes the result, and a human controls release.”

**Screen:** Architecture diagram; pause on the solid verified path.

## 0:55–1:15 — Architecture and Google stack

**Narration:**

“The live route runs three agents in Google ADK with Gemini 3.7 Flash and is deployed as a FastAPI service on Google Cloud Run. Deterministic Python tools calculate and verify the engineering result. SQLite demonstrates workflow persistence and restart/resume locally; I do not claim it is durable across Cloud Run instance replacement.”

**Screen:** Architecture, then agent registry. If Gemini or Cloud remains unverified, do not record the final video; the diagram currently labels those gates open.

## 1:15–2:25 — Actual execution

**Narration and actions:**

1. Show the live `.run` URL in the browser address bar and `GET /health` returning `google_cloud_deployment: true`.
2. Open `GET /agents` and show the three agent IDs, versions, bounded tools, data scopes, authority, and prohibited actions.
3. Invoke `POST /adk/live` with `UTL-NET-001_SYNTHETIC_INPUT.json`.
4. Show the verified Google ADK/Gemini trace: governing agent, routed delegation, engineering tool call, verification tool call, and final human-review requirement.
5. Show the structured result, agent/tool trace, calculation hash, verification hash, and `AWAITING_HUMAN_REVIEW` state.

**Narration:**

“The primary method is Darcy–Weisbach with Swamee–Jain. The independent verifier uses Haaland and requires every segment to agree within five percent. Here both endpoint residual pressures pass, and release remains blocked until review.”

## 2:25–2:55 — Persistence, restart, and human control

**Narration:**

“The same workflow identity can pause after engineering, reopen in a fresh process, resume at verification, and still cannot release itself. An attributable reviewer is required.”

**Screen:** One pre-recorded CLI sequence showing the same workflow ID at `PAUSED`, after fresh-process resume at `AWAITING_HUMAN_REVIEW`, and after the explicit demo-reviewer action.

## 2:55–3:20 — Fortified controls

**Narration:**

“The registry makes agents discoverable and versioned. SQLite preserves workflow identity, results, evidence hashes, and timestamped events across a fresh process. A worker handles queued work. Missing parameters are blocked instead of guessed, injected instructions are rejected again at tool boundaries, and traces contain actions and outcomes—never hidden chain-of-thought.”

**Screen:** Registry, current full-suite `OK` output, the blocked missing-input result, the blocked unallowlisted-context result, and the event trace.

## 3:20–3:38 — Google Cloud proof

**Narration:**

“This is the active Cloud Run revision, its deployment timestamp and image digest, followed by request logs for the exact invocation you just saw. The service is capped at one instance and scales to zero for cost control.”

**Screen:** Actual evidence for project `wexspace-agentic-2026`, service `wexspace-iew-agentic-fleet`, revision `wexspace-iew-agentic-fleet-00002-9tw`, live ADK HTTP 200, Vertex AI/ADC assertions, and the archive SHA-256. Use a Cloud Console capture if available; otherwise show the authentic structured evidence record rather than recreating a Cloud UI. Hide secrets and unrelated account data.

## 3:38–3:45 — Outcome

**Narration:**

“WEXSPACE AI makes engineering agents useful by making them bounded, reproducible, independently verifiable, and human-accountable.”

**Screen:** Released evidence summary and project name.

## Final validation before upload

- Duration is 3:20–3:50 and never exceeds 4:00.
- English audio or complete English subtitles.
- Publicly visible on YouTube or Vimeo; do not use private or unlisted visibility.
- The first 10–15 seconds show the real application working, not a title screen.
- Real live execution only; no fabricated log or hosted URL.
- Google Cloud proof is legible.
- Repository commit and diagram match the video.
- No API key, email, billing detail, private path, token, or employer/customer data is visible.
- URL opens in a signed-out browser.

Use [CLOUD_PROOF_CAPTURE_CHECKLIST.md](CLOUD_PROOF_CAPTURE_CHECKLIST.md) as the only Gate 7/video insertion checklist.
