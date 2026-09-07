# Agents for Humans 2026 — Competition Spec

Status: BUILD_READY_SPEC / NOT_FINAL_SUBMITTED  
Branch: `agents-for-humans-2026`  
Track target: **Professional Agents**

## Verified judging target
The submission must be a **new AI agent built with Strands Agents SDK** that does real work end-to-end for a real user. The strongest fit for WEXSPACE is a professional-work agent that reduces repetitive, judgment-heavy work while preserving explicit human decisions.

Judging dimensions:
1. Technological Implementation — real, non-trivial Strands usage; live demo and/or AgentCore deployment strengthens score.
2. Design — coherent product experience, not only a proof of concept.
3. Potential Impact — specific real problem and credible audience.
4. Creativity & Originality — non-obvious use of Strands and genuine domain understanding.
5. Presentation — clear end-to-end working demo and pitch.

## Challenge-new product
Working title: **WEXSPACE Professional Evidence Agent**

Primary user: independent professionals / engineers / technical consultants who receive incomplete work requests and lose time reconstructing scope, checking missing inputs, tracking progress, and packaging evidence.

Core workflow:
1. Intake a professional work request.
2. Normalize scope and required deliverables.
3. Detect missing/ambiguous inputs.
4. Build a bounded task plan.
5. Execute deterministic/local helper tools where applicable.
6. Persist an event cursor after every material state transition.
7. Produce an auditable evidence/deliverable package.
8. Surface only consequential decisions to the human.
9. Resume from interruption without restarting completed work.

## Judge-facing differentiator
Most agents demonstrate conversation. This entry should demonstrate **recoverable professional execution**:
- explicit state machine;
- resumable progress;
- evidence/provenance per atomic action;
- missing-input control;
- human-decision boundary;
- failure-safe resume;
- end-to-end outcome rather than chat-only output.

The shortest winning demonstration should show:
**request → missing-input detection → autonomous work → evidence → interruption/resume → human decision → final package**.

## Submission deliverables
- Public repository URL.
- MIT or Apache license visible in repository About section.
- README with cold-start setup.
- Architecture diagram file.
- AWS Builder ID.
- Demo video <= 5 minutes.
- Optional live demo.
- Optional builder.aws.com post titled with “Agents for Humans”.

## No-final-submit boundary
This branch may be built, tested, deployed, documented and prepared to SUBMIT_READY. Final Devpost submission remains user-controlled.
