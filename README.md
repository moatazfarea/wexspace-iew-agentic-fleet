# WEXSPACE AI — IEW Agentic Engineering Fleet

A governed three-agent workflow for auditable industrial engineering. The competition demo analyzes a fully synthetic cooling-water network, routes work through bounded agents, runs deterministic hydraulic equations, independently verifies the result, persists workflow state, and requires human approval before release.

Competition category: **Fortified Enterprise Fleet**  
Submission type: **Individual**  
Current state: **R07 governed core locally qualified; prior Gemini/ADK execution preserved; current-source live trace and Google Cloud deployment remain open**
Submission state: **not submitted**

## Why this exists

Industrial engineering work cannot safely rely on a chatbot inventing numerical answers. It needs explicit authority, reproducible equations, complete inputs, independent checking, durable state, operational traces, and accountable release. This project separates those responsibilities across the WEXSPACE Governing Agent, the IEW Engineering Specialist, and the WEXSPACE Verification / Evidence Specialist.

## Verified capability snapshot

| Capability | Current evidence-backed state |
|---|---|
| Python package and API | PASS locally |
| Google ADK | Current R07 local three-agent smoke PASS; historical authenticated execution PASS; current live trace open |
| Gemini 3.7 Flash | Historical direct execution PASS; current R07 route pinned to the Gemini Developer API |
| Cloud Run deployment | Prepared, NOT DEPLOYED — Google Cloud authentication/project unavailable |
| R07 three-agent routing and delegation | PASS locally through named WEXSPACE → IEW → verification roles |
| Deterministic engineering tool | PASS locally |
| Independent verification | PASS locally |
| SQLite persistence and restart/resume | PASS locally |
| Async queue/worker | PASS locally |
| Missing-input and prompt-injection controls | PASS locally |
| Human release gate | PASS locally |
| Isolated dependency environment | Current R07 source PASS (16/16); R03 fresh-install checkpoint PASS (14/14) |

The project preserves the prior verified Gemini response and ADK execution as historical evidence. It does not claim a current-source live three-agent Gemini trace, hosted URL, Cloud Run deployment, or cloud-persistent database until each is executed and captured against the current revision.

## Architecture

The [architecture diagram](architecture/architecture.svg) distinguishes verified local execution from external integrations that are implemented but not yet qualified. Its editable Mermaid source is in [architecture/architecture.mmd](architecture/architecture.mmd).

The primary local workflow is:

1. The WEXSPACE Governing Agent validates the explicit competition context allowlist, authority/relevance/scope compatibility, fixed goal, input completeness, and injection policy.
2. It records a delegation event to the IEW Engineering Specialist.
3. The specialist invokes a deterministic Darcy–Weisbach calculation using the Swamee–Jain friction approximation.
4. State and operational events are committed to SQLite.
5. The WEXSPACE Verification / Evidence Specialist independently recomputes with the Haaland approximation and checks agreement within 5%.
6. A human must approve the verified result before its state becomes `RELEASED`.

The live Google path uses a Google ADK `SequentialAgent` containing the same three roles, targets `gemini-3.7-flash`, explicitly pins the verified Gemini Developer API route (`GOOGLE_GENAI_USE_VERTEXAI=FALSE`), and exposes only three bounded deterministic tools. It is available at `POST /adk/live` when an API key is configured.

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
- For the live Gemini route: one environment variable named `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- For deployment: authenticated Google Cloud CLI, a user-approved billing-enabled project, Cloud Run API access, and a Secret Manager secret containing the Gemini API key

Never commit environment files or secret values.

## Reproducible local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

Expected test count for the R07 source revision: **16 tests**.

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

After setting an environment variable locally without writing it to the repository:

```bash
wexspace-adk live --input data/UTL-NET-001_SYNTHETIC_INPUT.json
```

If no key exists, the command exits nonzero with `BLOCKED_MISSING_GEMINI_API_KEY`. A PASS may only be recorded after the response and full three-agent trace are captured.

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

Reviewed evidence is stored under `evidence/`. Generated runtime databases and ad hoc logs are ignored. Every PASS in the compliance matrix must link to an executed artifact; unexecuted external gates remain `BLOCKED` or `USER_ACTION_REQUIRED`.

Known open gates:

- current-source live Gemini 3.7 Flash three-agent execution trace;
- authenticated Google Cloud project and Cloud Run deployment/invocation;
- visible Cloud deployment proof;
- GitHub repository creation/push and judge access as applicable;
- public video recording/upload and duration/language verification;
- organizer clarification and entrant self-verification for legal eligibility;
- Devpost draft verification and final submission authorization.

## Google technologies

- **Google Agent Development Kit:** historical authenticated and local execution verified; current R07 live trace open.
- **Gemini 3.7 Flash:** historical direct response verified; current R07 three-agent trace open.
- **Google Cloud Run:** deployment files prepared, deployment not yet verified.

Only technologies with completed evidence should be entered as actually used in the final Devpost fields.

## Deployment

Read [deployment/QUALIFICATION.md](deployment/QUALIFICATION.md). The guarded script requires explicit project, region, and Secret Manager names and must not be run until authentication, billing/cost authority, and secret configuration are confirmed.

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
