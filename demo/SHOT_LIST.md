# Recording shot list

| Time | View | Evidence that must be visible | Gate |
|---|---|---|---|
| 0:00–0:15 | Live Cloud Run result | `.run` URL or authentic readback record, HTTP 200, structured `/adk/live` result | immediate working proof |
| 0:15–0:35 | Synthetic input + problem | `SYNTHETIC` classification and engineering value | data policy/value |
| 0:35–0:55 | Architecture | three roles, deterministic tool, state, verifier, human gate | category fit |
| 0:55–1:15 | Architecture + registry | Google ADK, Gemini, Cloud labels, agent versions/scopes | stack + registry |
| 1:15–1:30 | `/agents` | three agent IDs and bounded scopes | discovery/security |
| 1:30–2:25 | `/adk/live` | Gemini 3.7 Flash and real three-agent/tool/result trace | mandatory tech/delegation |
| 2:25–2:55 | pause/restart/resume/review | same workflow ID through state transitions | persistence/human gate |
| 2:55–3:08 | negative controls | blocked missing input/injection/unallowlisted context | robustness |
| 3:08–3:20 | audit/provenance | timestamps, agent IDs, tool/result hashes | evidence |
| 3:20–3:38 | Real Cloud proof | service, revision, project, HTTP 200, log assertion, archive hash | cloud proof |
| 3:38–3:45 | released result | accepted + independently verified + approved | outcome |

Gemini and Cloud rows now have PASS evidence. The final take must use that authentic evidence and must not recreate a Cloud Console interface.
