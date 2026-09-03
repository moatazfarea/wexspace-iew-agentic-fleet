# WEXSPACE ProofDesk — WebMCP Challenge submission package

## One-line description

WEXSPACE ProofDesk turns browser-agent work into a bounded, visible, evidence-backed package that a deterministic gate can prepare—but only a human can release.

## Problem

Browser agents can act quickly, but high-consequence work becomes hard to trust when intent, evidence, verification, and release authority are hidden inside an automation trace. Teams need a shared surface where human intent is explicit, agent actions are constrained, evidence is inspectable, and release remains accountable.

## Solution

ProofDesk gives a human and a WebMCP browser agent one shared workspace. A human defines the deliverable contract. Five narrow site tools let an agent inspect the workspace, create the bounded work item, add criterion-linked HTTPS evidence, run a deterministic coverage gate, and prepare a passing package for review. The visible UI updates from the same domain state and audit ledger. No agent tool can approve or release the result.

## Why WebMCP

WebMCP makes the working website itself an explicit, typed agent interface. The agent does not scrape button labels or rely on brittle coordinates, and the human does not lose the visible product experience. Tool names, schemas, side effects, and authority boundaries are declared by the site, while both interaction modes reuse the same validation and state transitions.

## Better human–agent collaboration

Before ProofDesk, an agent can produce an answer or manipulate a page, but the human must reconstruct what was requested, which claims have evidence, whether acceptance criteria passed, and whether release occurred. ProofDesk makes that collaboration inspectable: one deliverable contract, one evidence set, one deterministic score, one audit history, and an explicit `AWAITING_HUMAN_REVIEW` boundary.

## What was built during the challenge

- the working WEXSPACE ProofDesk application;
- five imperative `document.modelContext.registerTool` WebMCP tools;
- a shared domain and validation layer for the human UI and site tools;
- deterministic evidence-coverage scoring;
- browser-local persistence and reload recovery;
- an auditable state-transition ledger;
- a human-only approval/revision boundary;
- unit, contract, rendering, and public judge-path tests;
- public deployment, documentation, evidence, and authentic demo recordings.

The WEXSPACE name and high-level governance ideas predate the challenge. Earlier WEXSPACE/IEW engineering work is unrelated prior work and is not presented as newly created here. See `PROVENANCE.md` for the exact boundary.

## Technology

- WebMCP draft API via `document.modelContext.registerTool`
- TypeScript, React, Vinext/Vite
- ChatGPT Sites public deployment
- browser `localStorage` for the versioned workspace and audit ledger
- Node test runner and ESLint

## Judge links

- Live application: https://wexspace-proofdesk.moatazalqobati20.chatgpt.site/
- Public competition source: https://github.com/moatazfarea/wexspace-iew-agentic-fleet/tree/webmcp-challenge-2026
- Runtime source commit: https://github.com/moatazfarea/wexspace-iew-agentic-fleet/commit/561df8f5bcfc40262af27706e0cc620878b738db
- Public video: pending verified publication

## Judge test path

Open the live application in the ChatGPT desktop in-app browser or Chrome 149+ with WebMCP testing enabled. Discover the five `wexspace.*` tools. Create a package with 2–6 acceptance criteria, add medium/high HTTPS evidence for every criterion, run the deterministic gate, then prepare human review. Confirm that the visible UI and tool response both show 100% coverage, `AWAITING_HUMAN_REVIEW`, and `releasePerformed: false`. Confirm there is no agent release tool.

## Security and limitations

ProofDesk requests no credentials and stores its workspace only in the current browser profile. Evidence URLs must use HTTPS. Evidence confidence is declared rather than independently fact-checked. This release supports one active package per browser profile, and native tool discovery requires a WebMCP-capable browser. ProofDesk is a governance and evidence workflow, not a professional certification authority.

## Submission state

The working application, public judge path, repository, license, tests, provenance, and written package are verified. The official public YouTube video and Devpost draft population remain open. Final Submit has not been performed.
