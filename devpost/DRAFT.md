# Devpost submission draft

Status: **prepared locally; existing Devpost draft could not be verified because the browser session is not authenticated. Do not create a second project. Do not final-submit without explicit user authorization.**

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

The demo accepts one neutral, synthetic cooling-water network. The governing engineering agent enforces a fixed purpose, checks required parameters, blocks prompt/tool injection patterns, records the workflow, and delegates the bounded calculation. The hydraulic specialist invokes Darcy–Weisbach equations with a Swamee–Jain friction approximation. The verification/evidence specialist independently recomputes with Haaland, checks continuity, velocity and residual-pressure rules, compares methods, and packages hashes and provenance. The result stops at a meaningful human approval gate before release.

The same workflow has a versioned agent registry, explicit data/tool/action scopes, timestamped operational traces, SQLite process-persistent state, restart/resume, and a bounded async queue/worker. The public fixture is synthetic and contains no employer or customer data.

## How we built it

- Python 3.12 for the engineering and workflow runtime.
- Google Agent Development Kit 2.8.0 for a three-agent sequential fleet. The real ADK runner is locally qualified; the live topology targets `gemini-3.5-flash` and exposes only three deterministic tools.
- FastAPI for agent discovery, workflow, worker, review, and live-ADK endpoints.
- SQLite for local persistent state, workflow identity, and operational events.
- Darcy–Weisbach, Swamee–Jain, and Haaland equations for reproducible calculation and independent validation.
- A guarded Docker/Cloud Run deployment path designed to scale to zero and read the Gemini key from Secret Manager.

Before final submission, replace the following sentence only if the corresponding evidence exists:

`[LIVE GOOGLE EVIDENCE PENDING: state the verified Gemini model response, Cloud Run revision, and cloud invocation here. Do not retain this bracketed note in the final submission.]`

## Challenges

The hardest design choice was keeping the model useful without allowing it to become the numerical authority. The project solves that by giving agents narrow orchestration and interpretation roles and reserving calculations for deterministic functions. A second challenge was distinguishing local persistence from cloud durability: this revision proves restart/resume with SQLite but does not mislabel Cloud Run's ephemeral filesystem as a durable cloud database. A third challenge was maintaining a strict boundary between pre-existing WEXSPACE/IEW ideas and new competition implementation.

## Accomplishments

- A real three-agent route with separated responsibilities and discoverable agent cards.
- Deterministic hydraulic analysis and an independent alternative-method verification.
- Explicit missing-input and injection failure paths.
- Persistent workflow identity that resumes in a fresh process.
- Background queue/worker behavior and a non-cosmetic human review gate.
- Structured traces and provenance hashes without exposing hidden chain-of-thought.
- Fourteen automated tests passing both in the working environment and after a fresh package installation.

Do not add live Gemini or Cloud accomplishments until those gates pass.

## What we learned

Agentic engineering is strongest when model reasoning, deterministic tools, workflow state, governance, and human accountability are visibly separate. Operational evidence matters as much as the final number: judges and engineers should be able to see who routed the task, which tool ran, what was persisted, how it was checked, and who approved release.

## What's next

The mandatory next steps are live Gemini 3.5 Flash execution, authenticated Cloud Run deployment and proof, repository publication/access verification, and a public English demo video. A future product revision could add a managed cloud state backend, stronger identity/policy enforcement, OpenTelemetry export, and additional neutral engineering specialists; none are claimed as implemented here.

## Data sources

Only a repository-owned synthetic cooling-water JSON fixture is used. Fluid properties and every network parameter are explicitly present in the input. No employer, customer, production, or personal dataset is used.

## Prior-work disclosure

The WEXSPACE AI / IEW AI vision, prior engineering methodologies, the earlier UTL-NET-001 workflow concept, and earlier persistence/evidence/orchestration concepts predate this project. The competition repository and its implementation, Google integrations, synthetic data, tests, controls, evidence, diagram, and submission assets are new during the submission period. Full machine-readable disclosure is included in the repository.

## Built with — current safe list

- Python
- FastAPI
- SQLite
- Google Agent Development Kit

Add **Gemini 3.5 Flash** only after a verified live model response. Add **Google Cloud Run** only after deployment and invocation evidence. Do not add Firestore; it is not implemented.

## Links — do not enter placeholders

- Repository URL: `OPEN — enter only after GitHub/GitLab/Bitbucket repository exists and access is verified`
- Hosted project URL: `OPEN — enter only after deployment and invocation verification; field is optional if unavailable`
- Video URL: `OPEN — enter only after public YouTube/Vimeo upload and validation`

## Testing instructions

Use the README's reproducible setup. Run `python -m unittest discover -s tests -v`, then execute the local workflow and ADK smoke. Live judges should invoke `/health`, `/agents`, `/workflows`, and `/adk/live` only after the submitted deployment evidence confirms access. Never place a secret or private credential in this text.
