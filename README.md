# WEXSPACE AI — IEW Agentic Engineering Fleet

A governed three-agent workflow for auditable industrial engineering. The competition demo analyzes a fully synthetic cooling-water network, routes work through bounded agents, runs deterministic hydraulic equations, independently verifies the result, persists workflow state, and requires human approval before release.

Competition category: **Fortified Enterprise Fleet**  
Submission type: **Individual**  
Current state: **canonical repository published; Vertex AI/ADC successor deployed and live-qualified on Cloud Run; final submission assets are being reconciled**
Submission state: **not submitted**

## Why this exists

Industrial engineering work cannot safely rely on a chatbot inventing numerical answers. It needs explicit authority, reproducible equations, complete inputs, independent checking, durable state, operational traces, and accountable release. This project separates those responsibilities across the WEXSPACE Governing Agent, the IEW Engineering Specialist, and the WEXSPACE Verification / Evidence Specialist.

## Verified capability snapshot

| Capability | Current evidence-backed state |
|---|---|
| Python package and API | PASS locally |
| Google ADK | PASS — deployed three-agent trace and all required agents/tools verified |
| Gemini 3.7 Flash | PASS — deployed through Vertex AI with Application Default Credentials |
| Cloud Run deployment | PASS — service `wexspace-iew-agentic-fleet`, revision `wexspace-iew-agentic-fleet-00002-9tw`, `us-central1` |
| Canonical repository | PUBLIC: `moatazfarea/wexspace-iew-agentic-fleet` |
| R07 three-agent routing and delegation | PASS locally through named WEXSPACE → IEW → verification roles |
| Deterministic engineering tool | PASS locally |
| Independent verification | PASS locally |
| SQLite persistence and restart/resume | PASS locally, including a current fresh-process qualification |
| Async queue/worker | PASS locally, including bounded no-duplicate worker proof |
| Missing-input and prompt-injection controls | PASS locally |
| Human release gate | PASS locally |
| Isolated dependency environment | Unaffected R07 baseline PASS (16/16); five affected live ADK checks PASS on the deployed successor |

The deployed successor is provenance-mapped to source commit `da70a9b7bb08280f9c5d3c450e2171f28dea6c96` and tree `6c572860fa041efde6b8bad8a19ed05d54465582`. The bounded live qualification returned HTTP 200, verified all three ADK agents and all bounded tools, and captured Cloud Run logs. The evidence archive SHA-256 is `7610a5a6d10bae2e7bae90939df572130669e507b686370880e232be64a0c20b`. This remains separate from the local SQLite restart/resume proof: no cloud-persistent database is claimed.

## Architecture

The [submission architecture diagram](architecture/architecture_submission.svg) distinguishes verified application execution, verified Drive continuity, open external deployment gates, and future managed services. A Devpost-ready [PNG render](architecture/architecture_submission.png) and editable [Mermaid source](architecture/architecture.mmd) are included.

The primary local workflow is:

1. The WEXSPACE Governing Agent validates the explicit competition context allowlist, authority/relevance/scope compatibility, fixed goal, input completeness, and injection policy.
2. It records a delegation event to the IEW Engineering Specialist.
3. The specialist invokes a deterministic Darcy–Weisbach calculation using the Swamee–Jain friction approximation.
4. State and operational events are committed to SQLite.
5. The WEXSPACE Verification / Evidence Specialist independently recomputes with the Haaland approximation and checks agreement within 5%.
6. A human must approve the verified result before its state becomes `RELEASED`.

The live Google path uses a Google ADK `SequentialAgent` containing the same three roles, targets `gemini-3.7-flash`, selects Vertex AI (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`), authenticates with the Cloud Run service identity through Application Default Credentials, and exposes only three bounded deterministic tools. It is deployed at `POST /adk/live`; the primary competition route does not require a Gemini API key.

## Repository map

```text
src/wexspace/       runtime, agents, Google ADK integration, equations, API
data/               synthetic demo input and a missing-input negative case
security/           versioned agent registry and agent cards
tests/              local, restart, async, security, API, and ADK tests
architecture/       source and rendered architecture diagram
deployment/         guarded Cloud Run deployment and qualification steps
evidence/           generated, reviewed qualification evidence
demo/               video script and recording plan
devpost/            accurate draft submission content
docs/               security, data control, and operating notes
```

## Prerequisites

- Python 3.11 or newer (qualified on Python 3.12.13)
- Internet access only for installing dependencies and for live Gemini/Cloud execution
- For the live Vertex route: `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION`, plus Application Default Credentials with Vertex access
- For deployment: authenticated Google Cloud CLI, the verified billing-enabled competition project, Cloud Run access, and the verified runtime service account

Never commit environment files or secret values.

## Reproducible local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

The preserved R07 baseline is **16/16 PASS**. The Vertex successor adds two focused routing tests; only the affected route and live five-check regression are requalified for this revision.

### Run the governed deterministic workflow

```bash
wexspace-fleet run --input data/UTL-NET-001_SYNTHETIC_INPUT.json
```

The result should stop at `AWAITING_HUMAN_REVIEW`. Release is a separate, attributable action:

```bash
wexspace-fleet approve WORKFLOW_ID --reviewer REVIEWER_ID
```

### Prove restart/resume

```bash
wexspace-fleet run --input data/UTL-NET-001_SYNTHETIC_INPUT.json --pause-after engineering
wexspace-fleet resume WORKFLOW_ID
```

Both commands use the same SQLite file, so the second fresh process reloads the workflow and resumes at verification.

### Prove background execution

```bash
wexspace-fleet queue --input data/UTL-NET-001_SYNTHETIC_INPUT.json
wexspace-fleet worker-once
```

### Run the local Google ADK framework proof

```bash
wexspace-adk smoke
```

This executes the real ADK runner and all three ADK agents using deterministic local model doubles. It deliberately reports `LOCAL_MODEL_DOUBLE_NO_GEMINI_CLAIM`.

### Run the eligible Gemini path

After configuring Vertex AI and Application Default Credentials without writing credentials to the repository:

```bash
wexspace-adk live --input data/UTL-NET-001_SYNTHETIC_INPUT.json
```

The qualified Cloud Run successor sets `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, project `wexspace-agentic-2026`, and location `global`. Its live response and three-agent trace passed the five affected checks: agents present, HTTP 200, model identity, overall ADK PASS, and bounded tools present. The API-key-backed Developer API implementation is retained only as an explicit legacy fallback and is not the primary competition route.

### Run the API

```bash
uvicorn wexspace.api:app --host 127.0.0.1 --port 8080
```

Key endpoints:

- `GET /health` — runtime health and accurate deployment indicator
- `GET /agents` — discoverable, versioned agent registry
- `POST /workflows` — governed deterministic workflow
- `POST /worker/once` — process one queued/paused workflow
- `POST /workflows/{id}/review` — attributable human release decision
- `POST /adk/live` — live Gemini 3.7 Flash workflow through Google ADK

## Engineering method

The demonstration uses steady, incompressible water flow in a directed acyclic synthetic network. The primary calculator applies Darcy–Weisbach pressure loss with Swamee–Jain friction factors. The verifier independently recomputes with Haaland. It also checks mass continuity, configured velocity limits, minimum residual pressure, endpoint count, and method agreement. All fluid properties and network parameters come from the input JSON; missing required values are blocked rather than guessed.

The synthetic example produces two endpoint paths. Local qualification observed residual pressures of 383.295650909 kPa at `HX-101` and 396.15525836 kPa at `HX-102`; those values are evidence from the deterministic tool, not model prose.

## Persistence and async behavior

SQLite stores workflow identity, current step, calculation, independent verification, evidence hashes, human review, and timestamped events. A second process can reopen the database and resume at the valid next step. A bounded worker processes queued or paused work.

Current limitation: the default Cloud Run filesystem is ephemeral. This revision proves process-level restart/resume locally but does **not** claim durable Cloud Run state across instance replacement. A managed cloud state backend is not shown as implemented.

## Security and data control

- Only the fixed synthetic cooling-water analysis goal is authorized.
- Context sources are denied by default unless their family is competition-allowlisted and authority, relevance, and scope compatibility all pass.
- Agent tool, data, action, and prohibited-action scopes are versioned in `security/agent_registry.json`.
- Required inputs are validated before routing.
- Common prompt/tool-injection strings are blocked at both workflow and ADK tool boundaries.
- Agents cannot execute shell commands, read arbitrary files, access secrets, or self-approve release.
- Operational traces record actions and outcomes, never hidden chain-of-thought.
- The repository contains neutral synthetic data only and no employer/customer production records.
- Secret, credential, PII, private-path, and employer-data scans are part of qualification.

See [docs/SECURITY_AND_DATA_CONTROL.md](docs/SECURITY_AND_DATA_CONTROL.md).

## Evidence and limitations

Reviewed evidence is indexed in [evidence/INDEX.md](evidence/INDEX.md). Generated runtime databases and ad hoc logs are ignored. Every PASS in the qualification matrix links to an executed or reopened artifact; unexecuted external gates remain open without fabricated proof.

The current [qualification matrix](evidence/FINAL_QUALIFICATION_MATRIX_R02.md) records fresh-process persistence/resume, bounded async behavior, registry authority, audit/provenance, the human gate, current publication scans, official-rule deltas, and the exact external boundaries. Direct dependency licensing is recorded in [docs/THIRD_PARTY_DEPENDENCY_LICENSE_REGISTER.json](docs/THIRD_PARTY_DEPENDENCY_LICENSE_REGISTER.json).

Known open submission gates:

- secondary registration of the private Cloud evidence object in the final evidence index;
- final documentation-only repository commit/readback verification;
- public video production/upload and duration/language verification;
- entrant confirmation of legal eligibility, ownership, and employer-policy compatibility;
- authenticated Devpost field reconciliation and final submission authorization.

## Google technologies

- **Google Agent Development Kit:** deployed three-agent execution verified.
- **Gemini 3.7 Flash:** deployed through Vertex AI and Cloud Run service identity/ADC.
- **Vertex AI:** primary deployed model backend; project `wexspace-agentic-2026`, location `global`.
- **Google Cloud Run:** deployed and invoked successfully in `us-central1`; active revision `wexspace-iew-agentic-fleet-00002-9tw`.

Only technologies with completed evidence should be entered as actually used in the final Devpost fields.

## Deployment

Read [deployment/QUALIFICATION.md](deployment/QUALIFICATION.md). The guarded script is pinned to the verified project, region, service identity, and scale-to-zero configuration; it removed the historical API-key secret binding from the successor service without deleting the historical secret. The deployed runtime source is explicitly separated from later documentation-only submission commits, so documentation changes do not trigger an unnecessary redeployment.

## Competition freeze rule

The official final-call update says the Devpost submission, linked repository, video, and other linked materials lock when the submission period ends at **2026-09-01 00:00 UTC**. After that point, this judged candidate must remain unchanged until winners are announced. Continued WEXSPACE development must use a separate post-competition branch or copy.

## Prior work and new work

The WEXSPACE AI / IEW AI vision, earlier engineering methodologies, the earlier UTL-NET-001 concept, and earlier persistence/evidence/orchestration concepts predate this competition. They are disclosed in [PRIOR_WORK_DISCLOSURE.md](PRIOR_WORK_DISCLOSURE.md) and [PRIOR_WORK_MANIFEST.json](PRIOR_WORK_MANIFEST.json).

This repository, its competition architecture, source code, Google ADK/Gemini/Cloud Run adapters, synthetic dataset, tests, controls, evidence package, diagram, and submission materials were created during the official submission period and are recorded in [HACKATHON_NEW_WORK_MANIFEST.json](HACKATHON_NEW_WORK_MANIFEST.json). No prior source code or confidential plant data was copied into this repository.

## Official references

- Rules: https://allthingsagentichackathon.devpost.com/rules
- FAQ: https://allthingsagentichackathon.devpost.com/details/faqs
- Resources: https://allthingsagentichackathon.devpost.com/resources
- Updates: https://allthingsagentichackathon.devpost.com/updates
- Gemini models: https://ai.google.dev/gemini-api/docs/models
- Google ADK workflow agents: https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/
- Cloud Run ADK deployment: https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-adk-service

## License and ownership

See [LICENSE](LICENSE). This competition repository grants no public reuse license. Final publication requires the entrant to confirm ownership, employer-policy compatibility, and the license basis of every incorporated component.
