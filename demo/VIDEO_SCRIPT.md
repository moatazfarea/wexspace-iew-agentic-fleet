# Demo video script — target 3:45

Status: **script and recording plan ready; recording/upload remain open until live Gemini and Cloud evidence exist.** Record in English or add complete English subtitles. Use one continuous execution where practical. Do not show fake logs, secret values, personal browser data, or functionality that did not pass.

## 0:00–0:25 — Problem and value

**Narration:**

“Industrial engineering work is more than producing an answer. Inputs must be complete, calculations reproducible, checks independent, decisions traceable, and consequential results released by an accountable human. WEXSPACE AI turns that workflow into a governed agent fleet.”

**Screen:** Title card, then the synthetic network JSON. Keep the word `SYNTHETIC` visible.

## 0:25–0:45 — Why a fleet, not a chatbot

**Narration:**

“A language model is not the numerical authority. One governing agent controls policy and routing. A bounded specialist invokes deterministic equations. A separate verification agent recomputes the result, and a human controls release.”

**Screen:** Architecture diagram; pause on the solid verified path.

## 0:45–1:10 — Architecture and Google stack

**Narration, only after live gates pass:**

“The live route runs three agents in Google ADK with Gemini 3.5 Flash and is deployed as a FastAPI service on Google Cloud Run. Deterministic Python tools calculate and verify the engineering result. SQLite demonstrates workflow persistence and restart/resume locally; I do not claim it is durable across Cloud Run instance replacement.”

**Screen:** Architecture, then agent registry. If Gemini or Cloud remains unverified, do not record the final video; the diagram currently labels those gates open.

## 1:10–2:40 — Unedited execution

**Narration and actions:**

1. Show the live `.run` URL in the browser address bar and `GET /health` returning `google_cloud_deployment: true`.
2. Open `GET /agents` and show the three agent IDs, versions, bounded tools, data scopes, authority, and prohibited actions.
3. Invoke `POST /adk/live` with `UTL-NET-001_SYNTHETIC_INPUT.json`.
4. Show the verified Google ADK/Gemini trace: governing agent, routed delegation, engineering tool call, verification tool call, and final human-review requirement.
5. Invoke the deterministic `/workflows` route with a pause after engineering if exposed for the demo, or show the CLI pause/resume in an adjacent terminal.
6. Show the workflow ID, `PAUSED`, reopen in a fresh process, resume to `AWAITING_HUMAN_REVIEW`, then approve with an attributable demo reviewer.

**Narration:**

“The primary method is Darcy–Weisbach with Swamee–Jain. The independent verifier uses Haaland and requires every segment to agree within five percent. Here both endpoint residual pressures pass, and release remains blocked until review.”

## 2:40–3:15 — Fortified controls

**Narration:**

“The registry makes agents discoverable and versioned. SQLite preserves workflow identity, results, evidence hashes, and timestamped events across a fresh process. A worker handles queued work. Missing parameters are blocked instead of guessed, injected instructions are rejected again at tool boundaries, and traces contain actions and outcomes—never hidden chain-of-thought.”

**Screen:** Registry, test output `14 tests ... OK`, the blocked missing-input result, and event trace.

## 3:15–3:38 — Google Cloud proof

**Narration, only with real evidence:**

“This is the active Cloud Run revision, its deployment timestamp and image digest, followed by request logs for the exact invocation you just saw. The service is capped at one instance and scales to zero for cost control.”

**Screen:** Google Cloud Console service/revision, project/region, log entries, then live `.run` response. Redact no material proof; hide only secrets and unrelated account data.

## 3:38–3:45 — Outcome

**Narration:**

“WEXSPACE AI makes engineering agents useful by making them bounded, reproducible, independently verifiable, and human-accountable.”

**Screen:** Released evidence summary and project name.

## Final validation before upload

- Duration is 3:20–3:50 and never exceeds 4:00.
- English audio or complete English subtitles.
- Publicly visible on YouTube or Vimeo, not private/unlisted if rules require public.
- Real live execution only; no fabricated log or hosted URL.
- Google Cloud proof is legible.
- Repository commit and diagram match the video.
- No API key, email, billing detail, private path, token, or employer/customer data is visible.
- URL opens in a signed-out browser.
