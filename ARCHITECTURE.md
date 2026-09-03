# Implemented architecture

WEXSPACE ProofDesk has one shared domain layer. Human controls and WebMCP tools do not maintain parallel business logic or hidden state.

```mermaid
flowchart TB
    subgraph Browser[Secure browser context]
        UI[Human workbench UI]
        WM[WebMCP tool adapter]
        CORE[Validated domain operations]
        STATE[Browser-local state + audit ledger]
        GATE[Deterministic acceptance gate]
        REVIEW[Human-only release control]
    end

    AGENT[Browser agent] --> WM
    HUMAN[Accountable human] --> UI
    WM --> CORE
    UI --> CORE
    CORE --> STATE
    CORE --> GATE
    GATE --> STATE
    STATE --> UI
    UI --> REVIEW
    WM -. no release capability .-> REVIEW
```

## Boundary table

| Boundary | Implemented behavior |
|---|---|
| Human input | Visible forms define intent, evidence, and review decisions. |
| Agent input | Five narrow WebMCP tools with JSON Schema inputs. |
| Shared execution | Both paths call `lib/proofdesk/domain.ts`. |
| Deterministic check | Required criteria are covered only by medium/high evidence. |
| Persistence | Versioned workspace is stored in browser `localStorage`. |
| Audit | Every material state transition records actor, time, action, and detail. |
| Release | Approval/rejection is available only in the human interface. |
| Unsupported browser | Human UI continues; capability status truthfully reports WebMCP unavailable. |

No backend AI service, hidden remote database, or autonomous release system is represented as implemented in this competition branch.
