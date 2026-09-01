# R19 PAE-006 Google-stack execution

This is an isolated adapter for the controlled study
`PAE006-FRESH-MOTIVE-AIR-SENSITIVITY-R01`. It preserves the existing UTL-NET-001
workflow and the same three WEXSPACE agent identities.

The live path is:

`WEXSPACE Governing Agent -> Google ADK -> gemini-3.7-flash on Vertex AI -> IEW
Engineering Specialist -> pae006_fresh_motive_air_sensitivity -> WEXSPACE
Verification / Evidence Specialist -> AWAITING_HUMAN_REVIEW`.

The deterministic tool creates the 12-point matrix, choking assessment, curve,
engineering conclusion, and SHA-256 manifest. The verifier recomputes mass flow
from critical-state density multiplied by sonic velocity. The wrapper refuses to
set the Google-stack gate to PASS unless all three agents and all three bounded
tools appear in the real ADK trace, the Vertex/ADC route is active on a qualified
Google surface, every artifact hash verifies, and release remains unperformed.

The Cloud Shell runner checks out a caller-pinned source commit in an isolated
worktree, runs only the affected R19 tests, invokes the real live fleet, writes
and reads back a compact Cloud Logging event, stores a hash-verified archive in
the existing R07 evidence bucket, and publishes only public-safe evidence to the
R19 branch. It does not redeploy Cloud Run or modify the existing UTL workflow.

The PAE-006 controlled basis predates this adapter. The R19 adapter, execution,
artifacts, and evidence are the fresh bounded work.

The generated values remain analytical motive-air estimates rather than tested
performance or a product rating. The controlled `Cd = 0.90` value is a working
assumption pending nozzle flow calibration.
