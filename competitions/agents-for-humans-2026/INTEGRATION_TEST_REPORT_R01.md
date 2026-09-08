# AFH Strands integration R01

17 targeted integration tests passed, with zero failures or errors, on 8 September 2026. The original five kernel tests were preserved and were not rerun. Kernel source is unchanged from the recorded base commit.

The tests run the real Strands 1.54.0 Agent, tool dispatch and FileSessionManager with a deterministic **test-only model**. No Gemini or other paid model request occurred. This is local integration evidence, not live provider or deployment qualification.

The receiving reconciliation uses bounded synthetic CSV inputs, exact decimal arithmetic, SQLite transactions, event hashes, evidence hashes and operation receipts. A child process exits abruptly after committed work. A fresh process restores cursor 6, reuses the original three evidence objects even after source files are removed, and advances to cursor 8 and human review without repeating reconciliation.

Additional checks cover missing inputs, concurrent duplicate requests, invalid CSV rollback, path restrictions, altered evidence, human approval/rejection and early model termination. The human action is a trusted local operator CLI boundary; a reviewer string is not remote authentication.

See `evidence/INTEGRATION_R01.json` for measured properties, source hashes, raw-evidence digest and limits, and `evidence/integration-r01.junit.xml` for individual results. The public XML omits the private execution hostname; its original digest is retained in the JSON record. The original terminal recording was reopened and hash-checked during recovery; it is not graphical video.

This capsule delta was authored with ChatGPT/Codex assistance under the participant's authorization. Gemini did not produce or execute this delta. It is isolated from Agentic Cinema and does not promote universal SPINE-002 to complete.

Pending: live authenticated Gemini invocation, persistent cloud runtime, qualified live video, deployment invocation, functioning demo and final submission preparation. Final competition submission remains user-only.
