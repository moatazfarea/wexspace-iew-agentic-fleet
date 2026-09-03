export type Actor = "HUMAN" | "AGENT" | "SYSTEM"

export type WorkStatus =
  | "NO_WORK_ITEM"
  | "IN_PROGRESS"
  | "GATE_FAILED"
  | "GATE_PASSED"
  | "AWAITING_HUMAN_REVIEW"
  | "RELEASED"
  | "REVISION_REQUIRED"

export type Confidence = "LOW" | "MEDIUM" | "HIGH"

export interface AcceptanceCriterion {
  id: string
  label: string
  required: true
}

export interface WorkItem {
  id: string
  title: string
  objective: string
  primaryDeliverable: string
  criteria: AcceptanceCriterion[]
  createdAt: string
}

export interface EvidenceItem {
  id: string
  title: string
  sourceUrl: string
  summary: string
  criterionId: string
  confidence: Confidence
  createdAt: string
  actor: Actor
}

export interface GateResult {
  passed: boolean
  score: number
  coveredCriteria: string[]
  missingCriteria: string[]
  checkedAt: string
}

export interface AuditEvent {
  id: string
  timestamp: string
  actor: Actor
  action: string
  detail: string
}

export interface WorkspaceState {
  schemaVersion: "1.0"
  revision: number
  status: WorkStatus
  workItem: WorkItem | null
  evidence: EvidenceItem[]
  gate: GateResult | null
  releasePerformed: boolean
  reviewNote: string | null
  audit: AuditEvent[]
}

export interface CreateWorkItemInput {
  title: string
  objective: string
  primaryDeliverable: string
  criteria: string[]
}

export interface AddEvidenceInput {
  title: string
  sourceUrl: string
  summary: string
  criterionId: string
  confidence: Confidence
}

export class DomainError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.name = "DomainError"
    this.code = code
  }
}

const MAX_AUDIT_EVENTS = 100

function makeId(prefix: string): string {
  const uuid = globalThis.crypto?.randomUUID?.()
  return `${prefix}_${uuid ?? `${Date.now()}_${Math.random().toString(16).slice(2)}`}`
}

function now(): string {
  return new Date().toISOString()
}

function cleanText(value: unknown, field: string, min: number, max: number): string {
  if (typeof value !== "string") {
    throw new DomainError("INVALID_INPUT", `${field} must be text.`)
  }

  const cleaned = value.trim().replace(/\s+/g, " ")
  if (cleaned.length < min || cleaned.length > max) {
    throw new DomainError(
      "INVALID_INPUT",
      `${field} must contain between ${min} and ${max} characters.`,
    )
  }
  return cleaned
}

function requireHttpsUrl(value: unknown): string {
  const cleaned = cleanText(value, "Source URL", 8, 500)
  let url: URL
  try {
    url = new URL(cleaned)
  } catch {
    throw new DomainError("INVALID_SOURCE", "Source URL must be a valid HTTPS URL.")
  }
  if (url.protocol !== "https:") {
    throw new DomainError("INVALID_SOURCE", "Source URL must use HTTPS.")
  }
  return url.toString()
}

function appendAudit(
  state: WorkspaceState,
  actor: Actor,
  action: string,
  detail: string,
  timestamp = now(),
): AuditEvent[] {
  const event: AuditEvent = {
    id: makeId("evt"),
    timestamp,
    actor,
    action,
    detail: cleanText(detail, "Audit detail", 1, 320),
  }
  return [event, ...state.audit].slice(0, MAX_AUDIT_EVENTS)
}

export function createInitialState(): WorkspaceState {
  const timestamp = now()
  const initial: WorkspaceState = {
    schemaVersion: "1.0",
    revision: 0,
    status: "NO_WORK_ITEM",
    workItem: null,
    evidence: [],
    gate: null,
    releasePerformed: false,
    reviewNote: null,
    audit: [],
  }
  return {
    ...initial,
    audit: appendAudit(initial, "SYSTEM", "WORKSPACE_INITIALIZED", "A new local workspace was created.", timestamp),
  }
}

export function createWorkItem(
  state: WorkspaceState,
  input: CreateWorkItemInput,
  actor: Actor,
): WorkspaceState {
  const title = cleanText(input.title, "Title", 4, 100)
  const objective = cleanText(input.objective, "Objective", 12, 600)
  const primaryDeliverable = cleanText(
    input.primaryDeliverable,
    "Primary deliverable",
    6,
    220,
  )

  if (!Array.isArray(input.criteria)) {
    throw new DomainError("INVALID_INPUT", "Criteria must be an array of text values.")
  }

  const uniqueCriteria = Array.from(
    new Map(
      input.criteria.map((criterion) => {
        const cleaned = cleanText(criterion, "Criterion", 4, 180)
        return [cleaned.toLocaleLowerCase(), cleaned]
      }),
    ).values(),
  )

  if (uniqueCriteria.length < 2 || uniqueCriteria.length > 6) {
    throw new DomainError("INVALID_INPUT", "Provide between 2 and 6 distinct acceptance criteria.")
  }

  const timestamp = now()
  const workItem: WorkItem = {
    id: makeId("work"),
    title,
    objective,
    primaryDeliverable,
    criteria: uniqueCriteria.map((label) => ({
      id: makeId("criterion"),
      label,
      required: true,
    })),
    createdAt: timestamp,
  }

  const next: WorkspaceState = {
    ...state,
    revision: state.revision + 1,
    status: "IN_PROGRESS",
    workItem,
    evidence: [],
    gate: null,
    releasePerformed: false,
    reviewNote: null,
  }
  return {
    ...next,
    audit: appendAudit(
      next,
      actor,
      "WORK_ITEM_CREATED",
      `Created “${title}” with ${workItem.criteria.length} required criteria.`,
      timestamp,
    ),
  }
}

export function addEvidence(
  state: WorkspaceState,
  input: AddEvidenceInput,
  actor: Actor,
): WorkspaceState {
  if (!state.workItem) {
    throw new DomainError("NO_WORK_ITEM", "Create a work item before adding evidence.")
  }
  if (state.releasePerformed) {
    throw new DomainError("RELEASED", "Released work is immutable in this workspace.")
  }

  const criterion = state.workItem.criteria.find((item) => item.id === input.criterionId)
  if (!criterion) {
    throw new DomainError("UNKNOWN_CRITERION", "The selected acceptance criterion does not exist.")
  }

  if (!(["LOW", "MEDIUM", "HIGH"] as const).includes(input.confidence)) {
    throw new DomainError("INVALID_INPUT", "Confidence must be LOW, MEDIUM, or HIGH.")
  }

  const timestamp = now()
  const evidence: EvidenceItem = {
    id: makeId("evidence"),
    title: cleanText(input.title, "Evidence title", 4, 120),
    sourceUrl: requireHttpsUrl(input.sourceUrl),
    summary: cleanText(input.summary, "Evidence summary", 20, 800),
    criterionId: criterion.id,
    confidence: input.confidence,
    createdAt: timestamp,
    actor,
  }

  const next: WorkspaceState = {
    ...state,
    revision: state.revision + 1,
    status: "IN_PROGRESS",
    evidence: [...state.evidence, evidence],
    gate: null,
    reviewNote: null,
  }
  return {
    ...next,
    audit: appendAudit(
      next,
      actor,
      "EVIDENCE_ADDED",
      `Added “${evidence.title}” to criterion “${criterion.label}”.`,
      timestamp,
    ),
  }
}

export function runAcceptanceGate(state: WorkspaceState, actor: Actor): WorkspaceState {
  if (!state.workItem) {
    throw new DomainError("NO_WORK_ITEM", "Create a work item before running the gate.")
  }
  if (state.releasePerformed) {
    throw new DomainError("RELEASED", "Released work is immutable in this workspace.")
  }

  const coveredCriteria = state.workItem.criteria
    .filter((criterion) =>
      state.evidence.some(
        (item) => item.criterionId === criterion.id && item.confidence !== "LOW",
      ),
    )
    .map((criterion) => criterion.id)

  const missingCriteria = state.workItem.criteria
    .filter((criterion) => !coveredCriteria.includes(criterion.id))
    .map((criterion) => criterion.id)

  const score = Math.round((coveredCriteria.length / state.workItem.criteria.length) * 100)
  const timestamp = now()
  const gate: GateResult = {
    passed: missingCriteria.length === 0,
    score,
    coveredCriteria,
    missingCriteria,
    checkedAt: timestamp,
  }

  const next: WorkspaceState = {
    ...state,
    revision: state.revision + 1,
    status: gate.passed ? "GATE_PASSED" : "GATE_FAILED",
    gate,
    reviewNote: null,
  }
  return {
    ...next,
    audit: appendAudit(
      next,
      actor,
      "ACCEPTANCE_GATE_RUN",
      gate.passed
        ? `Gate passed at ${score}% required-criterion coverage.`
        : `Gate failed at ${score}% coverage; ${missingCriteria.length} required criterion or criteria remain.`,
      timestamp,
    ),
  }
}

export function prepareHumanReview(state: WorkspaceState, actor: Actor): WorkspaceState {
  if (!state.workItem || !state.gate?.passed || state.status !== "GATE_PASSED") {
    throw new DomainError(
      "GATE_NOT_PASSED",
      "A current passing acceptance gate is required before human review.",
    )
  }

  const timestamp = now()
  const next: WorkspaceState = {
    ...state,
    revision: state.revision + 1,
    status: "AWAITING_HUMAN_REVIEW",
    releasePerformed: false,
  }
  return {
    ...next,
    audit: appendAudit(
      next,
      actor,
      "HUMAN_REVIEW_REQUESTED",
      "The package was queued for accountable human review; no release was performed.",
      timestamp,
    ),
  }
}

export function recordHumanDecision(
  state: WorkspaceState,
  decision: "APPROVE" | "REQUEST_REVISION",
  note: string,
): WorkspaceState {
  if (state.status !== "AWAITING_HUMAN_REVIEW") {
    throw new DomainError("NOT_AWAITING_REVIEW", "This package is not awaiting human review.")
  }

  const cleanNote = cleanText(note, "Review note", 4, 400)
  const timestamp = now()
  const approved = decision === "APPROVE"
  const next: WorkspaceState = {
    ...state,
    revision: state.revision + 1,
    status: approved ? "RELEASED" : "REVISION_REQUIRED",
    releasePerformed: approved,
    reviewNote: cleanNote,
  }
  return {
    ...next,
    audit: appendAudit(
      next,
      "HUMAN",
      approved ? "RELEASE_APPROVED" : "REVISION_REQUESTED",
      approved
        ? "An accountable human approved release from the visible interface."
        : "An accountable human returned the package for revision.",
      timestamp,
    ),
  }
}

export function getAllowedNextActions(state: WorkspaceState): string[] {
  if (!state.workItem) return ["create_work_item"]
  if (state.status === "RELEASED") return ["inspect_workspace"]
  if (state.status === "AWAITING_HUMAN_REVIEW") return ["inspect_workspace", "human_review_in_ui"]
  if (state.status === "GATE_PASSED") {
    return ["inspect_workspace", "add_evidence", "run_acceptance_gate", "prepare_human_review"]
  }
  return ["inspect_workspace", "add_evidence", "run_acceptance_gate"]
}

export function inspectWorkspace(state: WorkspaceState) {
  const criteria = state.workItem?.criteria.map((criterion) => ({
    id: criterion.id,
    label: criterion.label,
    covered:
      state.evidence.some(
        (item) => item.criterionId === criterion.id && item.confidence !== "LOW",
      ) ?? false,
  })) ?? []

  return {
    schemaVersion: state.schemaVersion,
    revision: state.revision,
    status: state.status,
    workItem: state.workItem
      ? {
          id: state.workItem.id,
          title: state.workItem.title,
          objective: state.workItem.objective,
          primaryDeliverable: state.workItem.primaryDeliverable,
        }
      : null,
    criteria,
    evidenceCount: state.evidence.length,
    gate: state.gate,
    releasePerformed: state.releasePerformed,
    allowedNextActions: getAllowedNextActions(state),
  }
}

export function restoreWorkspaceState(raw: string | null): WorkspaceState | null {
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as Partial<WorkspaceState>
    if (
      parsed.schemaVersion !== "1.0" ||
      typeof parsed.revision !== "number" ||
      !Array.isArray(parsed.evidence) ||
      !Array.isArray(parsed.audit) ||
      typeof parsed.releasePerformed !== "boolean"
    ) {
      return null
    }
    return parsed as WorkspaceState
  } catch {
    return null
  }
}
