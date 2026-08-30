# Cloud Run deployment and qualification

Status: **PASS — Vertex AI successor deployed and live-qualified**.

The verified competition project and Cloud Run service identity use Vertex AI through Application Default Credentials. The primary deployment does not inject a Gemini API key. The historical Secret Manager secret is retained but not attached to the successor revision. The service scales to zero and caps instances at one, but that is not a guarantee of zero cost.

Verified deployed identity:

- project: `wexspace-agentic-2026`
- service: `wexspace-iew-agentic-fleet`
- region: `us-central1`
- ready revision: `wexspace-iew-agentic-fleet-00002-9tw`
- deployed source commit: `da70a9b7bb08280f9c5d3c450e2171f28dea6c96`
- deployed source tree: `6c572860fa041efde6b8bad8a19ed05d54465582`
- backend: Vertex AI, `gemini-3.7-flash`
- credential source: Application Default Credentials using the Cloud Run service identity
- live ADK HTTP status: `200`
- evidence archive SHA-256: `7610a5a6d10bae2e7bae90939df572130669e507b686370880e232be64a0c20b`

## Required environment-variable names

- `GOOGLE_CLOUD_PROJECT`
- `CLOUD_RUN_REGION`
- `GOOGLE_CLOUD_LOCATION`
- `SERVICE_ACCOUNT_EMAIL`

## Deploy

From the repository root:

```bash
bash deployment/deploy_cloud_run.sh
```

## Qualification sequence

1. Capture `gcloud run services describe wexspace-iew-agentic-fleet` with project, region, revision, image digest, and service URL.
2. Open the Cloud Run dashboard and capture the service, active revision, timestamp, and Google Cloud project identity without exposing credentials.
3. Invoke `GET /health`; verify `google_cloud_deployment` is `true`.
4. Invoke `GET /agents`; verify three discoverable versioned records.
5. Invoke `POST /workflows` with the synthetic input; capture the structured local workflow result.
6. Invoke `POST /adk/live` with the same input; require a successful `gemini-3.7-flash` three-agent trace and confirm `VERTEX_AI`, `APPLICATION_DEFAULT_CREDENTIALS`, project `wexspace-agentic-2026`, and location `global`.
7. Capture Cloud Run request/application logs for both invocations.
8. Re-run missing-input and prompt-injection cases against the service.
9. Save raw command output, request/response bodies, revision identity, timestamps, and SHA-256 hashes in the bounded Cloud evidence archive.
10. Register the evidence pointer and archive hash in the final evidence index after secondary readback.

The bounded successor script reruns only the five previously failed live checks and captures the service, revision, invocation, and log proof:

```bash
EXPECTED_COMMIT=VERIFIED_SUCCESSOR_COMMIT \
EXPECTED_TREE=VERIFIED_SUCCESSOR_TREE \
bash deployment/qualify_vertex_cloud_run.sh
```

The executed successor passed `adk_agents_present`, `adk_http_200`, `adk_model`, `adk_pass`, and `adk_tools_present`. It also verified Vertex AI/ADC routing, project/location, service-account identity, absence of API-key environment variables, presence of relevant logs, and no logged secret values. The historical Gemini Developer API 429 route was superseded and was not retried.

## Accurate limitations

The SQLite file under `/tmp` is suitable for one bounded demonstration instance but is not durable across Cloud Run instance replacement. Do not describe it as cloud-persistent state. The local restart/resume proof is separate. A managed persistent backend is not implemented in this revision.
