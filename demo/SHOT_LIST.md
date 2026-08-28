# Recording shot list

| Time | View | Evidence that must be visible | Gate |
|---|---|---|---|
| 0:00–0:25 | Title + synthetic input | Project title; `SYNTHETIC` classification | data policy |
| 0:25–0:45 | Architecture | three roles, deterministic tool, state, verifier, human gate | category fit |
| 0:45–1:10 | Architecture + registry | Google ADK, verified Gemini/Cloud labels, agent versions/scopes | stack + registry |
| 1:10–1:25 | Live Cloud Run URL | `.run` address and `/health` deployment flag | cloud invocation |
| 1:25–1:40 | `/agents` | three agent IDs and bounded scopes | discovery/security |
| 1:40–2:15 | `/adk/live` | Gemini 3.5 Flash and real three-agent/tool trace | mandatory tech/delegation |
| 2:15–2:40 | pause/restart/resume/review | same workflow ID through state transitions | persistence/human gate |
| 2:40–3:00 | negative tests + test suite | blocked missing input/injection; 14 tests OK | robustness |
| 3:00–3:15 | audit/provenance | timestamps, agent IDs, tool/result hashes | evidence |
| 3:15–3:38 | Cloud Console + logs | service, revision, project, timestamp, request log | cloud proof |
| 3:38–3:45 | released result | accepted + independently verified + approved | outcome |

Do not record the final take until the Gemini and Cloud rows have genuine PASS evidence.
