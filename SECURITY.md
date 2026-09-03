# Security and control model

## Data handled

ProofDesk accepts a bounded work objective, acceptance criteria, evidence summaries, HTTPS source URLs, and a human review note. It does not request credentials, cookies, API keys, payment data, or identity documents.

## WebMCP controls

- Tools expose only parameters needed for the active workflow.
- All tool schemas set `additionalProperties: false` and constrain string/array sizes.
- Tool descriptions state mutations and important preconditions.
- `wexspace.inspect_workspace` is marked read-only.
- Evidence output is marked untrusted because it may contain user- or source-supplied content.
- The tool catalog deliberately excludes human approval and release.
- Domain validation is shared by the UI and tool paths, preventing a weaker agent-only path.
- Abort signals unregister tools when the client component is disposed.

## Persistence

State is stored locally in the browser under `wexspace-proofdesk.workspace.v1`. It is not uploaded by this version. Users can remove it through browser storage controls. Released work is immutable in the active workspace.

## Known limitations

- A user or agent can provide a misleading evidence summary or confidence label; ProofDesk records provenance but does not fact-check the source.
- Browser storage is not a multi-user database and does not provide cryptographic non-repudiation.
- WebMCP is a draft platform API whose support and security behavior depend on the host browser.
- The application is a governance aid, not an authorization system or professional certification authority.

Security reports should include a reproducible description without live credentials or private user data.
