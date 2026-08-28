# Cloud Run deployment and qualification

Status: **prepared but not deployed**.

Do not execute these steps until the entrant has authenticated, selected an approved billing-enabled project, confirmed any cost exposure, and created a Secret Manager secret. The script scales to zero and caps instances at one, but that is not a guarantee of zero cost.

## Required environment-variable names

- `GOOGLE_CLOUD_PROJECT`
- `CLOUD_RUN_REGION`
- `GOOGLE_API_KEY_SECRET` (secret name, not secret value)

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
6. Invoke `POST /adk/live` with the same input; require a successful `gemini-3.5-flash` three-agent trace.
7. Capture Cloud Run request/application logs for both invocations.
8. Re-run missing-input and prompt-injection cases against the service.
9. Save console screenshot(s), raw command output, request/response bodies, revision identity, timestamps, and SHA-256 hashes under `evidence/cloud/`.
10. Update the compliance matrix only after independent review of those artifacts.

## Accurate limitations

The SQLite file under `/tmp` is suitable for one bounded demonstration instance but is not durable across Cloud Run instance replacement. Do not describe it as cloud-persistent state. The local restart/resume proof is separate. A managed persistent backend is not implemented in this revision.
