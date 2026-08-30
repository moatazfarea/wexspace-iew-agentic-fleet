# Devpost submission draft

Status: **repository and Cloud facts are reconciled; the public video URL and authenticated existing-project field entry remain open. Do not create a second project. Do not final-submit without explicit user authorization.**

## Existing draft values to preserve and verify

- Project: `WEXSPACE AI — IEW Agentic Engineering Fleet`
- Submitter type: `Individual`
- Country: `Yemen`
- Category: `Fortified Enterprise Fleet`
- Start date shown by the user: `08-29-26`
- Startup Excellence: `NOT SELECTED`

The filesystem records show the competition workspace was created at `2026-08-28T23:03:16Z`, which is August 28 in Pacific time. The displayed `08-29-26` date may reflect the entrant's local date. Verify the field truthfully; do not change it merely for appearance.

## Project title

WEXSPACE AI — IEW Agentic Engineering Fleet

## Tagline

A governed three-agent industrial engineering fleet that delegates deterministic analysis, independently verifies every result, persists state, and requires human release.

## Short summary

WEXSPACE AI turns a high-consequence engineering calculation into a governed, auditable agent workflow. A governing agent validates policy and inputs, delegates a synthetic cooling-water analysis to a bounded specialist, and routes the deterministic result to an independent verification agent. Persistent workflow state, restart/resume, async execution, scoped tools, provenance hashes, and a human release gate make the system an enterprise fleet rather than a chatbot.

## Inspiration

Industrial engineers spend significant time gathering parameters, running repeatable calculations, checking work, recording assumptions, and reconstructing decisions after interruptions. A conversational answer is not enough when numbers affect equipment and operations. The project explores an unlikely but high-value enterprise use case for agents: institutional engineering workflows where AI coordinates work while deterministic tools remain the numerical authority.

## What it does

The demo accepts one neutral, synthetic cooling-water network. The WEXSPACE Governing Agent enforces the competition context allowlist, authority/relevance/scope compatibility, fixed purpose, required parameters, and prompt/tool-injection controls before it delegates the bounded calculation. The IEW Engineering Specialist invokes Darcy–Weisbach equations with a Swamee–Jain friction approximation. The WEXSPACE Verification / Evidence Specialist independently recomputes with Haaland, checks continuity, velocity and residual-pressure rules, compares methods, and packages hashes and provenance. The result stops at a meaningful human approval gate before release.

The same workflow has a versioned agent registry, explicit data/tool/action scopes, timestamped operational traces, SQLite process-persistent state, restart/resume, and a bounded async queue/worker. The public fixture is synthetic and contains no employer or customer data.

## How we built it

- Python 3.12 for the engineering and workflow runtime.
- Google Agent Development Kit for a three-agent sequential fleet. The deployed topology targets `gemini-3.7-flash` through Vertex AI with Cloud Run service identity/ADC and exposes only three deterministic tools.
- FastAPI for agent discovery, workflow, worker, review, and live-ADK endpoints.
- SQLite for local persistent state, workflow identity, and operational events.
- Darcy–Weisbach, Swamee–Jain, and Haaland equations for reproducible calculation and independent validation.
- A guarded Docker/Cloud Run deployment that scales to zero, caps instances at one, and uses Vertex AI through the runtime service identity without a primary API-key dependency.

The live successor runs in Google Cloud project `wexspace-agentic-2026` on Cloud Run service `wexspace-iew-agentic-fleet`, region `us-central1`, revision `wexspace-iew-agentic-fleet-00002-9tw`. Its `/adk/live` endpoint returned HTTP 200 and verified the three required ADK agents, bounded tools, `gemini-3.7-flash` model identity, Vertex AI backend, and Application Default Credentials. The deployed source is commit `da70a9b7bb08280f9c5d3c450e2171f28dea6c96`, tree `6c572860fa041efde6b8bad8a19ed05d54465582`.

## Challenges

The hardest design choice was keeping the model useful without allowing it to become the numerical authority. The project solves that by giving agents narrow orchestration and interpretation roles and reserving calculations for deterministic functions. A second challenge was distinguishing local persistence from cloud durability: this revision proves restart/resume with SQLite but does not mislabel Cloud Run's ephemeral filesystem as a durable cloud database. A third challenge was maintaining a strict boundary between pre-existing WEXSPACE/IEW ideas and new competition implementation.

## Accomplishments

- A real three-agent route with separated responsibilities and discoverable agent cards.
- Deterministic hydraulic analysis and an independent alternative-method verification.
- Explicit missing-input and injection failure paths.
- Persistent workflow identity that resumes in a fresh process.
- Background queue/worker behavior and a non-cosmetic human review gate.
- Structured traces and provenance hashes without exposing hidden chain-of-thought.
- Sixteen automated tests passing against the current R07 source in an isolated dependency environment; the earlier R03 checkpoint also preserved a 14/14 fresh-install PASS.
- A live Google ADK three-agent trace using Gemini 3.7 Flash through Vertex AI and ADC on Google Cloud Run.
- A readback-verified Cloud evidence archive with SHA-256 `7610a5a6d10bae2e7bae90939df572130669e507b686370880e232be64a0c20b` and no secret values logged.

## What we learned

Agentic engineering is strongest when model reasoning, deterministic tools, workflow state, governance, and human accountability are visibly separate. Operational evidence matters as much as the final number: judges and engineers should be able to see who routed the task, which tool ran, what was persisted, how it was checked, and who approved release.

## What's next

The next product revision could add a managed cloud state backend, managed enterprise identity/policy services, OpenTelemetry export, and additional neutral engineering specialists; none are claimed as implemented here. The competition submission itself still requires public video publication, final Devpost field reconciliation, and explicit user authorization before final submit.

## Data sources

Only a repository-owned synthetic cooling-water JSON fixture is used. Fluid properties and every network parameter are explicitly present in the input. No employer, customer, production, or personal dataset is used.

## Prior-work disclosure

The WEXSPACE AI / IEW AI vision, prior engineering methodologies, the earlier UTL-NET-001 workflow concept, and earlier persistence/evidence/orchestration concepts predate this project. The competition repository and its implementation, Google integrations, synthetic data, tests, controls, evidence, diagram, and submission assets are new during the submission period. Full machine-readable disclosure is included in the repository.

## Built with — current safe list

- Python
- FastAPI
- SQLite
- Google Agent Development Kit
- Gemini 3.7 Flash
- Vertex AI
- Google Cloud Run

Do not add Firestore or other managed products; they are not implemented.

## Links — do not enter placeholders

- Repository URL: `https://github.com/moatazfarea/wexspace-iew-agentic-fleet`
- Hosted project URL: omit unless the exact service URL is independently recovered; the official guidance treats this field as encouraged rather than mandatory.
- Video URL: `OPEN — enter only after public YouTube/Vimeo upload and validation`

## Testing instructions

Use the README's reproducible setup. Run `python -m unittest discover -s tests -v`, then execute the local workflow and ADK smoke. Live judges may invoke `/health`, `/agents`, `/workflows`, and `/adk/live` while the submitted Cloud Run service remains available. Never place a secret or private credential in this text.

## Official lock warning

Before the deadline the draft may be updated as often as needed. At **2026-09-01 00:00 UTC**, the submitted form and all linked materials must remain unchanged until winners are announced. Post-deadline WEXSPACE work belongs on a separate continuation branch or copy.
