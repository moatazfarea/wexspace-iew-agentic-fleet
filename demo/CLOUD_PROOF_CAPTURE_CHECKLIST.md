# Cloud proof capture checklist

Use this only after a real deployment succeeds. It is the single insertion point for Gate 7 evidence and the final video.

## Identity frame

- Google Cloud project ID `wexspace-agentic-2026` is legible.
- Cloud Run service name, region, active revision, deployment timestamp, and container/image digest are legible.
- The candidate Git commit is shown adjacent to the deployment evidence.
- Secrets, billing details, account email, unrelated projects, and private browser data are not visible.

## Invocation frame

- The real `.run` URL is visible in the browser address bar.
- `GET /health` returns a successful status and `google_cloud_deployment: true`.
- `GET /agents` returns the three named, versioned, bounded agents.
- `POST /workflows` returns the structured deterministic result and the human-review hold.
- `POST /adk/live` returns a successful `gemini-3.7-flash` Google ADK trace with governing delegation, deterministic calculation, independent verification, and structured evidence.

## Logs frame

- Cloud Run request/application logs show the same service revision and invocation time.
- Request status is successful and can be correlated to the captured response without logging secret values.
- The evidence package includes raw response bodies, service/revision metadata, relevant logs, timestamps, and SHA-256 hashes.

## Video insertion

- Use the immediate `.run` proof at 0:00–0:15 and the full invocation at 1:15–2:25 in `VIDEO_SCRIPT.md`.
- Use the Cloud Console revision and logs at 3:20–3:38.
- Keep the final video at or below four minutes, publicly visible on YouTube or Vimeo, and in English or fully subtitled in English.
- Verify the public video URL in a signed-out browser before entering it in Devpost.

No Cloud label changes from `OPEN` to `PASS` until every identity, invocation, log, and durable-evidence item above is captured.
