import {
  addEvidence,
  createWorkItem,
  inspectWorkspace,
  prepareHumanReview,
  runAcceptanceGate,
  type AddEvidenceInput,
  type CreateWorkItemInput,
  type WorkspaceState,
} from "./domain"

export interface WebMcpToolDefinition {
  name: string
  title: string
  description: string
  inputSchema: Record<string, unknown>
  execute: (input: Record<string, unknown>) => Promise<unknown>
  annotations?: {
    readOnlyHint?: boolean
    untrustedContentHint?: boolean
  }
}

export interface ModelContextLike {
  registerTool: (
    tool: WebMcpToolDefinition,
    options?: { signal?: AbortSignal },
  ) => Promise<void> | void
}

export interface ProofDeskRuntime {
  getState: () => WorkspaceState
  commit: (operation: (state: WorkspaceState) => WorkspaceState) => WorkspaceState
}

export type WebMcpRegistrationResult =
  | { status: "AVAILABLE"; toolCount: number; unregister: () => void }
  | { status: "UNAVAILABLE"; toolCount: 0; reason: string }

function toolResponse(operation: () => WorkspaceState) {
  try {
    const state = operation()
    return {
      ok: true,
      workspace: inspectWorkspace(state),
    }
  } catch (error) {
    return {
      ok: false,
      error: {
        name: error instanceof Error ? error.name : "Error",
        message: error instanceof Error ? error.message : "Unknown tool execution error.",
      },
    }
  }
}

export function buildProofDeskTools(runtime: ProofDeskRuntime): WebMcpToolDefinition[] {
  return [
    {
      name: "wexspace.inspect_workspace",
      title: "Inspect WEXSPACE workspace",
      description:
        "Read the current work item, acceptance coverage, release state, and allowed next actions. This tool does not modify state.",
      inputSchema: {
        type: "object",
        properties: {},
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: false },
      execute: async () => ({ ok: true, workspace: inspectWorkspace(runtime.getState()) }),
    },
    {
      name: "wexspace.create_work_item",
      title: "Create governed work item",
      description:
        "Create or replace the active bounded work item. This clears existing evidence and requires two to six explicit acceptance criteria.",
      inputSchema: {
        type: "object",
        required: ["title", "objective", "primaryDeliverable", "criteria"],
        additionalProperties: false,
        properties: {
          title: { type: "string", minLength: 4, maxLength: 100 },
          objective: { type: "string", minLength: 12, maxLength: 600 },
          primaryDeliverable: { type: "string", minLength: 6, maxLength: 220 },
          criteria: {
            type: "array",
            minItems: 2,
            maxItems: 6,
            uniqueItems: true,
            items: { type: "string", minLength: 4, maxLength: 180 },
          },
        },
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute: async (input) =>
        toolResponse(() =>
          runtime.commit((state) =>
            createWorkItem(state, input as unknown as CreateWorkItemInput, "AGENT"),
          ),
        ),
    },
    {
      name: "wexspace.add_evidence",
      title: "Add claim-linked evidence",
      description:
        "Add one HTTPS source and concise evidence summary mapped to an existing acceptance criterion. This modifies the visible workspace.",
      inputSchema: {
        type: "object",
        required: ["title", "sourceUrl", "summary", "criterionId", "confidence"],
        additionalProperties: false,
        properties: {
          title: { type: "string", minLength: 4, maxLength: 120 },
          sourceUrl: { type: "string", format: "uri", minLength: 8, maxLength: 500 },
          summary: { type: "string", minLength: 20, maxLength: 800 },
          criterionId: { type: "string", minLength: 4, maxLength: 100 },
          confidence: { type: "string", enum: ["LOW", "MEDIUM", "HIGH"] },
        },
      },
      annotations: { readOnlyHint: false, untrustedContentHint: true },
      execute: async (input) =>
        toolResponse(() =>
          runtime.commit((state) =>
            addEvidence(state, input as unknown as AddEvidenceInput, "AGENT"),
          ),
        ),
    },
    {
      name: "wexspace.run_acceptance_gate",
      title: "Run deterministic acceptance gate",
      description:
        "Recompute required-criterion evidence coverage with deterministic application logic and store the result in the audit ledger.",
      inputSchema: {
        type: "object",
        properties: {},
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute: async () =>
        toolResponse(() => runtime.commit((state) => runAcceptanceGate(state, "AGENT"))),
    },
    {
      name: "wexspace.prepare_human_review",
      title: "Prepare accountable human review",
      description:
        "After a current passing gate, move the package to AWAITING_HUMAN_REVIEW. This tool cannot approve or release work.",
      inputSchema: {
        type: "object",
        properties: {},
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute: async () =>
        toolResponse(() => runtime.commit((state) => prepareHumanReview(state, "AGENT"))),
    },
  ]
}

export async function registerProofDeskTools(
  modelContext: ModelContextLike | undefined,
  runtime: ProofDeskRuntime,
): Promise<WebMcpRegistrationResult> {
  if (!modelContext?.registerTool) {
    return {
      status: "UNAVAILABLE",
      toolCount: 0,
      reason: "This browser has not exposed document.modelContext.",
    }
  }

  const controller = new AbortController()
  const tools = buildProofDeskTools(runtime)
  await Promise.all(
    tools.map((tool) => modelContext.registerTool(tool, { signal: controller.signal })),
  )

  return {
    status: "AVAILABLE",
    toolCount: tools.length,
    unregister: () => controller.abort(),
  }
}
