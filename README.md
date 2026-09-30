# WEXSPACE AI — Shipaton 2026 Next Gen

WEXSPACE AI is a human-governed AI execution workspace for work that must survive interruptions, remain auditable, and preserve the distinction between **configured**, **authorized**, **executed**, and **verified** state.

This branch is the public source package being prepared for the **RevenueCat Shipaton 2026 — Next Gen** submission.

## Judge path

The Android product demonstrates the same governed execution model across short specialist workflows:

- **Engineering** — deterministic work with reproducible results and evidence.
- **Software / QA** — governed checks, tasks, state, and evidence.
- **Studio OS** — media-production orchestration using scenes, capture, evidence, and QA.

The submission film uses a real automated Android-emulator capture. The raw runtime capture included under `submission/` is hash-bound; no purchase success or external provider success is simulated.

## Android / RevenueCat

The Shipaton Android source is under:

`mobile/shipaton2026/`

The module currently includes RevenueCat Android SDK **10.15.1** and a bounded entitlement adapter:

- Test Store configuration for the sandbox flavor.
- Galaxy configuration for the Galaxy flavor.
- offering fetch / purchase path.
- CustomerInfo entitlement refresh.
- restore-purchases path.
- entitlement identifier: `pro`.
- visible `Unlock Pro` and `Restore` product controls.

A RevenueCat account/project, product, entitlement and offering must still be live-qualified before claiming a successful purchase. The demo must not fabricate that state.

## Reproducible Android build

Prerequisites:

- JDK 17
- Android SDK 36
- Gradle compatible with the project

For a RevenueCat Test Store build, provide your own public Test Store SDK key as the environment variable expected by the Gradle configuration:

`REVENUECAT_TEST_API_KEY`

Then build the sandbox debug variant from `mobile/shipaton2026`.

Do not commit private credentials.

## Evidence / media

Current submission media:

- `submission/wexspace-runtime.mp4` — real Android-emulator runtime capture.
- `submission/wexspace-runtime-meta.txt` — SHA-256 and size receipt.
- `submission/render-shipaton-final.sh` — reproducible cinematic render script.
- `submission/WEXSPACE_SHIPATON_NEXTGEN_R02.mp4` — 115-second cinematic submission candidate with timed narration and captions.\n- `submission/WEXSPACE_SHIPATON_NEXTGEN_R02.sha256` and `.meta.json` — final film integrity and duration receipts.

The real Android capture is based on a disposable emulator and a local deterministic fixture; it does **not** prove real Google OAuth, external model inference, or RevenueCat purchase execution.

## Broader WEXSPACE direction

WEXSPACE is being built as a multi-domain execution platform. Engineering is the first specialist domain. Studio OS applies the same execution, evidence, continuity, and human-authority model to production workflows.

## Security and authority

WEXSPACE does not treat a configured capability as an executed one. Consequential actions remain behind explicit authority boundaries. Runtime evidence is separated from design intent and historical evidence.

## License

See [LICENSE](LICENSE). Third-party components remain subject to their own licenses.

## Submission status

The Devpost project is **WEXSPACE AI**. Final submission is not claimed by this repository until a Devpost submission receipt exists.
