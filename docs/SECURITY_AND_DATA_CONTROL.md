# Security and data control

## Data classification

| Data | Classification | Allowed readers | Allowed mutation | Retention |
|---|---|---|---|---|
| Synthetic network JSON | PUBLIC_SAFE_SYNTHETIC | all three bounded agents | none after workflow creation | repository fixture and workflow record |
| Calculation result | PUBLIC_SAFE_SYNTHETIC | governing, engineering, verification | deterministic tool creates; no agent edits | workflow record/evidence |
| Verification result | PUBLIC_SAFE_SYNTHETIC | governing and verification | verification tool creates; no agent edits | workflow record/evidence |
| Workflow state/events | CONTROLLED_DEMO | governing workflow; read-only status API | state store methods only | SQLite until operator deletion |
| Reviewer identifier | CONTROLLED_DEMO | governing workflow and evidence reviewer | one approval event | SQLite/evidence |
| API keys/credentials | SECRET | SDK/runtime only | never by an agent | environment/Secret Manager, never repository |

## Authority boundaries

The registry is the public control plane. Every agent has a version, purpose, contract, allowed tools, allowed data, allowed actions, and prohibited actions. The governing agent may route/block/pause/resume but cannot calculate or release without review. The engineering specialist may calculate only. The verifier may independently verify/reject/request review but cannot change or approve a result.

## Injection and input controls

Untrusted strings are treated as data. A fixed goal allowlist prevents arbitrary tasks. A small denylist blocks common attempts to override policy, reveal secrets, execute commands, or disable controls. The check is applied before the custom workflow routes and again inside ADK deterministic tool boundaries. Structural and numeric validation rejects missing/invalid parameters rather than filling them with model guesses.

This denylist is a minimum competition control, not a complete production content-security system.

## Secrets

Only environment-variable names are documented. Secret values are never logged. `.env`, private keys, runtime databases, and ad hoc runtime logs are ignored. Cloud deployment is designed to bind `GOOGLE_API_KEY` from Secret Manager by secret name.

## Auditability and human control

Events record workflow ID, timestamp, agent identity, action type, outcome, and structured details. Details include hashes and tool identities, not hidden chain-of-thought. A verified calculation becomes `AWAITING_HUMAN_REVIEW`; only a nonempty attributable reviewer decision promotes it to `RELEASED`.

## Known limitations

- The policy detector is intentionally small and demonstrative.
- SQLite access is process-local and has no tenant authentication layer.
- Cloud Run's default filesystem is ephemeral; cloud-durable state is not claimed.
- No UI or identity provider is implemented.
- Live Gemini and Cloud behavior remain unqualified until external credentials and deployment evidence exist.
