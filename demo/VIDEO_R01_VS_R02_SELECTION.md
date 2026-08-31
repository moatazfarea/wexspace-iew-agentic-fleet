# Final competition video selection

Selected candidate: **VIDEO_R02**.

| Criterion | VIDEO_R01 fallback | VIDEO_R02 selected |
|---|---:|---:|
| Duration | 225.0 s | 219.9 s |
| 1080p H.264 | PASS | PASS |
| English subtitle track | PASS | PASS |
| Verified Cloud identities | PASS | PASS |
| Continuous authentic WEXSPACE execution | proof summary only | **72.066667 s, no cuts** |
| Governing → IEW → deterministic tool → verifier → human gate visible | static evidence | **committed application events visible** |
| Actual engineering outputs visible | static summary | **live stdout from the real workflow** |
| R01 preserved as fallback | n/a | PASS |

R02 materially improves Proof of Action without changing runtime source, dependencies, deployment configuration, or previously qualified behavior. Its live segment launches the production `AgentFleet`; the media-only state-store observer prints records only after SQLite commits them. The Cloud segment reads the authentic public-safe record of the direct Cloud Run/Vertex qualification and does not fabricate a Cloud Console interface.

R01 remains unchanged at SHA-256 `cf158113fca3028379f45a6c1052aa6f863c9f3d7a22717ed435b3d5cc2a946e` and is retained solely as a deadline fallback.
