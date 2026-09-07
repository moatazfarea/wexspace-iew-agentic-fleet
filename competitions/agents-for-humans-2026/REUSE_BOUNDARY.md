# Prior Work / New Work Boundary

## Prior WEXSPACE work
The following are pre-existing concepts or historical implementations and must be disclosed rather than represented as new:
- WEXSPACE governance and multi-domain architecture.
- IEW engineering specialist lineage.
- ProofDesk/evidence concepts.
- historical checkpoint/provenance practices.
- prior Google/Devpost competition code and deployment artifacts.

## New work for Agents for Humans
The competition entry on branch `agents-for-humans-2026` must implement a new Strands-based Professional Agents application during the hackathon period.

New implementation scope should include:
- Strands agent runtime and tool layer;
- challenge-specific work-intake contract;
- event cursor + resumable state implementation for this agent;
- professional-work evidence package generation;
- human decision surfacing;
- challenge-specific tests/evaluations;
- challenge-specific UI/demo surface if used;
- challenge-specific deployment configuration;
- challenge-specific architecture diagram, README and demo.

## Reuse rule
Conceptual patterns may be reused. Code is reused only when allowed by the competition rules and explicitly disclosed. The safest default for judge-facing critical-path components is a fresh implementation with a clear lineage note.

## Cross-opportunity promotion
Any component proven on this branch may later be promoted into WEXSPACE Core only after:
1. tests pass;
2. provenance is recorded;
3. interfaces are generalized;
4. challenge-specific dependencies are separated behind adapters;
5. no competition-specific rule restricts reuse.
