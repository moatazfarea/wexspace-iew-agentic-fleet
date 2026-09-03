"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  Activity,
  ArrowRight,
  Bot,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileCheck2,
  Link as LinkIcon,
  LockKeyhole,
  Plus,
  ShieldCheck,
  UserRound,
  XCircle,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import {
  addEvidence,
  createInitialState,
  createWorkItem,
  inspectWorkspace,
  prepareHumanReview,
  recordHumanDecision,
  restoreWorkspaceState,
  runAcceptanceGate,
  type Confidence,
  type WorkspaceState,
} from "@/lib/proofdesk/domain"
import {
  registerProofDeskTools,
  type ModelContextLike,
} from "@/lib/proofdesk/webmcp"

declare global {
  interface Document {
    modelContext?: ModelContextLike
  }
}

const STORAGE_KEY = "wexspace-proofdesk.workspace.v1"

const sampleCase = {
  title: "Public API release evidence package",
  objective:
    "Prepare a bounded evidence package that proves a public API release is functional, documented, secure, and ready for accountable review.",
  primaryDeliverable: "Verified API release evidence package",
  criteria: [
    "Production endpoint returns a successful response",
    "Public documentation explains the supported workflow",
    "Secret scan reports no exposed credentials",
  ],
}

const statusCopy: Record<WorkspaceState["status"], string> = {
  NO_WORK_ITEM: "No package",
  IN_PROGRESS: "In progress",
  GATE_FAILED: "Evidence gaps",
  GATE_PASSED: "Gate passed",
  AWAITING_HUMAN_REVIEW: "Awaiting human review",
  RELEASED: "Released by human",
  REVISION_REQUIRED: "Revision required",
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The operation could not be completed."
}

export function Workbench() {
  const [workspace, setWorkspace] = useState<WorkspaceState>(() => createInitialState())
  const workspaceRef = useRef(workspace)
  const [hydrated, setHydrated] = useState(false)
  const [webMcp, setWebMcp] = useState<{
    status: "CHECKING" | "AVAILABLE" | "UNAVAILABLE" | "ERROR"
    detail: string
  }>({ status: "CHECKING", detail: "Checking this browser…" })
  const [notice, setNotice] = useState("Ready for a human or browser agent to begin.")

  const [title, setTitle] = useState(sampleCase.title)
  const [objective, setObjective] = useState(sampleCase.objective)
  const [primaryDeliverable, setPrimaryDeliverable] = useState(sampleCase.primaryDeliverable)
  const [criteria, setCriteria] = useState(sampleCase.criteria.join("\n"))

  const [evidenceTitle, setEvidenceTitle] = useState("")
  const [sourceUrl, setSourceUrl] = useState("")
  const [summary, setSummary] = useState("")
  const [criterionId, setCriterionId] = useState("")
  const [confidence, setConfidence] = useState<Confidence>("HIGH")
  const [reviewNote, setReviewNote] = useState("")

  const commit = useCallback((operation: (state: WorkspaceState) => WorkspaceState) => {
    const next = operation(workspaceRef.current)
    workspaceRef.current = next
    setWorkspace(next)
    return next
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const restored = restoreWorkspaceState(window.localStorage.getItem(STORAGE_KEY))
      if (restored) {
        workspaceRef.current = restored
        setWorkspace(restored)
        setNotice("Recovered the last local workspace revision.")
      }
      setHydrated(true)
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (!hydrated) return
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace))
  }, [hydrated, workspace])

  useEffect(() => {
    if (!hydrated) return
    let unregister: (() => void) | undefined
    let disposed = false

    registerProofDeskTools(document.modelContext, {
      getState: () => workspaceRef.current,
      commit,
    })
      .then((result) => {
        if (disposed) {
          if (result.status === "AVAILABLE") result.unregister()
          return
        }
        if (result.status === "AVAILABLE") {
          unregister = result.unregister
          setWebMcp({
            status: "AVAILABLE",
            detail: `${result.toolCount} site tools active`,
          })
        } else {
          setWebMcp({ status: "UNAVAILABLE", detail: result.reason })
        }
      })
      .catch((error) => {
        if (!disposed) {
          setWebMcp({ status: "ERROR", detail: errorMessage(error) })
        }
      })

    return () => {
      disposed = true
      unregister?.()
    }
  }, [commit, hydrated])

  const criterionById = useMemo(
    () => new Map(workspace.workItem?.criteria.map((item) => [item.id, item.label]) ?? []),
    [workspace.workItem],
  )

  const coverage = workspace.gate?.score ?? 0
  const inspection = inspectWorkspace(workspace)
  const latestAuditEvent = workspace.audit[0]
  const liveAgent =
    latestAuditEvent?.actor === "AGENT"
      ? "Browser agent"
      : latestAuditEvent?.actor === "HUMAN"
        ? "Accountable human"
        : "Workspace core"
  const liveSurface = latestAuditEvent?.actor === "AGENT" ? "WebMCP + browser" : "Human application"
  const activeCriterionId =
    workspace.workItem?.criteria.some((criterion) => criterion.id === criterionId)
      ? criterionId
      : (workspace.workItem?.criteria[0]?.id ?? "")

  function handleCreateWorkItem() {
    try {
      const next = commit((state) =>
        createWorkItem(
          state,
          {
            title,
            objective,
            primaryDeliverable,
            criteria: criteria.split("\n").filter((item) => item.trim()),
          },
          "HUMAN",
        ),
      )
      setCriterionId(next.workItem?.criteria[0]?.id ?? "")
      setNotice("Work item created. Evidence can now be added by a human or site tool.")
    } catch (error) {
      setNotice(errorMessage(error))
    }
  }

  function handleAddEvidence() {
    try {
      commit((state) =>
        addEvidence(
          state,
          { title: evidenceTitle, sourceUrl, summary, criterionId: activeCriterionId, confidence },
          "HUMAN",
        ),
      )
      setEvidenceTitle("")
      setSourceUrl("")
      setSummary("")
      setNotice("Evidence added and the previous gate result invalidated.")
    } catch (error) {
      setNotice(errorMessage(error))
    }
  }

  function handleGate() {
    try {
      const next = commit((state) => runAcceptanceGate(state, "HUMAN"))
      setNotice(
        next.gate?.passed
          ? "Acceptance gate passed. The package can be prepared for human review."
          : `Gate failed: ${next.gate?.missingCriteria.length ?? 0} criterion or criteria need stronger evidence.`,
      )
    } catch (error) {
      setNotice(errorMessage(error))
    }
  }

  function handlePrepareReview() {
    try {
      commit((state) => prepareHumanReview(state, "HUMAN"))
      setNotice("Package is awaiting accountable human review. No release was performed.")
    } catch (error) {
      setNotice(errorMessage(error))
    }
  }

  function handleHumanDecision(decision: "APPROVE" | "REQUEST_REVISION") {
    try {
      commit((state) => recordHumanDecision(state, decision, reviewNote))
      setNotice(
        decision === "APPROVE"
          ? "Release approved by the human reviewer."
          : "Package returned for revision by the human reviewer.",
      )
    } catch (error) {
      setNotice(errorMessage(error))
    }
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/80 bg-background/95 px-4 py-3 backdrop-blur sm:px-6">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl border border-primary/30 bg-primary/10 text-primary">
              <ShieldCheck aria-hidden="true" className="size-5" />
            </div>
            <div>
              <p className="text-lg font-semibold tracking-tight">WEXSPACE ProofDesk</p>
              <p className="text-sm text-muted-foreground">Governed human–agent evidence workbench</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="gap-1.5 border-border bg-card/70 px-3 py-1.5">
              <span
                aria-hidden="true"
                className={`size-2 rounded-full ${
                  webMcp.status === "AVAILABLE"
                    ? "bg-emerald-400"
                    : webMcp.status === "CHECKING"
                      ? "bg-amber-300"
                      : "bg-zinc-500"
                }`}
              />
              {webMcp.status === "AVAILABLE" ? webMcp.detail : "Human UI active"}
            </Badge>
            <Badge className="bg-primary/15 px-3 py-1.5 text-primary" variant="secondary">
              {statusCopy[workspace.status]}
            </Badge>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1500px] gap-4 p-4 sm:p-6 lg:grid-cols-[330px_minmax(0,1fr)_330px]">
        <aside className="space-y-4">
          <section className="surface-panel p-4">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="eyebrow">Deliverable contract</p>
                <h1 className="mt-1 text-xl font-semibold">Define the work</h1>
              </div>
              <ClipboardCheck aria-hidden="true" className="size-5 text-primary" />
            </div>
            <div className="space-y-3">
              <label className="field-label" htmlFor="work-title">Work item</label>
              <Input
                id="work-title"
                maxLength={100}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />

              <label className="field-label" htmlFor="work-objective">Objective</label>
              <Textarea
                id="work-objective"
                maxLength={600}
                rows={4}
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
              />

              <label className="field-label" htmlFor="primary-deliverable">Primary deliverable</label>
              <Input
                id="primary-deliverable"
                maxLength={220}
                value={primaryDeliverable}
                onChange={(event) => setPrimaryDeliverable(event.target.value)}
              />

              <label className="field-label" htmlFor="acceptance-criteria">
                Acceptance criteria <span className="text-muted-foreground">(one per line)</span>
              </label>
              <Textarea
                id="acceptance-criteria"
                maxLength={900}
                rows={5}
                value={criteria}
                onChange={(event) => setCriteria(event.target.value)}
              />

              <Button className="w-full" onClick={handleCreateWorkItem}>
                {workspace.workItem ? "Replace active work item" : "Create work item"}
                <ArrowRight aria-hidden="true" />
              </Button>
              <p className="text-xs leading-5 text-muted-foreground">
                Replacing a work item clears its evidence. Site tools use this same operation.
              </p>
            </div>
          </section>

          <section className="surface-panel p-4">
            <div className="flex items-start gap-3">
              <Bot aria-hidden="true" className="mt-0.5 size-5 text-primary" />
              <div>
                <p className="font-medium">WebMCP execution plane</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">{webMcp.detail}</p>
                <p className="mt-3 text-xs leading-5 text-muted-foreground">
                  In a supported browser, an agent can inspect, create, add evidence, run the gate,
                  and prepare review. It cannot release the result.
                </p>
              </div>
            </div>
          </section>
        </aside>

        <section className="min-w-0 space-y-4">
          <div className="surface-panel overflow-hidden">
            <div className="border-b border-border/80 p-4 sm:p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="eyebrow">Active package</p>
                  <h2 className="mt-1 text-2xl font-semibold tracking-tight">
                    {workspace.workItem?.title ?? "Create a work item to begin"}
                  </h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                    {workspace.workItem?.objective ??
                      "The human UI remains fully functional even when this browser does not expose WebMCP."}
                  </p>
                </div>
                <div className="min-w-[170px] rounded-xl border border-border bg-background/50 p-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Coverage</span>
                    <span className="font-mono font-semibold text-primary">{coverage}%</span>
                  </div>
                  <Progress className="mt-2" value={coverage} />
                  <p className="mt-2 text-xs text-muted-foreground">Revision {workspace.revision}</p>
                </div>
              </div>
            </div>

            <details className="mx-4 mt-4 rounded-2xl border border-border bg-background/35" data-testid="live-execution-panel">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
                <span className="flex min-w-0 items-center gap-2">
                  <span aria-hidden="true" className="size-2 shrink-0 rounded-full bg-emerald-400 shadow-[0_0_0_4px_rgba(110,240,180,0.1)]" />
                  <span className="font-mono text-xs font-semibold tracking-[0.16em] text-primary">
                    LIVE EXECUTION
                  </span>
                </span>
                <Badge variant="outline">{statusCopy[workspace.status]}</Badge>
              </summary>
              <div className="grid gap-3 border-t border-border px-4 py-4 sm:grid-cols-2 xl:grid-cols-4">
                <div>
                  <p className="eyebrow">Current agent</p>
                  <p className="mt-1 text-sm font-medium">{liveAgent}</p>
                </div>
                <div>
                  <p className="eyebrow">Current action</p>
                  <p className="mt-1 break-words font-mono text-xs font-semibold text-primary">
                    {latestAuditEvent?.action ?? "NO_ACTION"}
                  </p>
                </div>
                <div>
                  <p className="eyebrow">Execution surface</p>
                  <p className="mt-1 text-sm font-medium">{liveSurface}</p>
                </div>
                <div>
                  <p className="eyebrow">Checkpoint</p>
                  <p className="mt-1 font-mono text-sm font-semibold">Revision {workspace.revision}</p>
                </div>
                <div>
                  <p className="eyebrow">Evidence</p>
                  <p className="mt-1 text-sm font-medium">{workspace.evidence.length} linked item(s)</p>
                </div>
                <div>
                  <p className="eyebrow">RCS</p>
                  <p className="mt-1 text-sm font-medium">None active in this package</p>
                </div>
                <div className="sm:col-span-2">
                  <p className="eyebrow">Recording</p>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">
                    Not controlled by this site. External session capture is governed and verified separately.
                  </p>
                </div>
              </div>
            </details>

            <Tabs defaultValue="workspace" className="gap-0">
              <TabsList className="mx-4 mt-4" variant="line">
                <TabsTrigger value="workspace">Workspace</TabsTrigger>
                <TabsTrigger value="evidence">Evidence ({workspace.evidence.length})</TabsTrigger>
                <TabsTrigger value="audit">Audit ({workspace.audit.length})</TabsTrigger>
              </TabsList>

              <TabsContent className="p-4 sm:p-5" value="workspace">
                {workspace.workItem ? (
                  <div className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">
                    <section>
                      <div className="mb-3 flex items-center justify-between">
                        <h3 className="font-semibold">Required acceptance criteria</h3>
                        <Badge variant="outline">{workspace.workItem.criteria.length} required</Badge>
                      </div>
                      <div className="space-y-2">
                        {workspace.workItem.criteria.map((criterion, index) => {
                          const covered = inspection.criteria.find((item) => item.id === criterion.id)?.covered
                          return (
                            <article className="criterion-row" key={criterion.id}>
                              <span className="criterion-index">{String(index + 1).padStart(2, "0")}</span>
                              <p className="min-w-0 flex-1 text-sm leading-6">{criterion.label}</p>
                              {covered ? (
                                <CheckCircle2 aria-label="Covered" className="size-5 text-emerald-400" />
                              ) : (
                                <XCircle aria-label="Not covered" className="size-5 text-muted-foreground" />
                              )}
                            </article>
                          )
                        })}
                      </div>
                      <div className="mt-4 rounded-xl border border-border bg-background/45 p-4">
                        <p className="eyebrow">Native output</p>
                        <p className="mt-1 font-medium">{workspace.workItem.primaryDeliverable}</p>
                      </div>
                    </section>

                    <section className="rounded-2xl border border-border bg-background/35 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="eyebrow">Deterministic gate</p>
                          <h3 className="mt-1 text-lg font-semibold">
                            {workspace.gate
                              ? workspace.gate.passed
                                ? "All required criteria covered"
                                : `${workspace.gate.missingCriteria.length} evidence gap(s)`
                              : "Not run yet"}
                          </h3>
                        </div>
                        <FileCheck2 aria-hidden="true" className="size-5 text-primary" />
                      </div>
                      <p className="mt-3 text-sm leading-6 text-muted-foreground">
                        Medium- or high-confidence evidence must cover every required criterion.
                        The result is computed by application logic, not model arithmetic.
                      </p>
                      <div className="mt-4 grid gap-2">
                        <Button variant="outline" onClick={handleGate}>
                          <Activity aria-hidden="true" />
                          Run gate
                        </Button>
                        <Button
                          disabled={!workspace.gate?.passed || workspace.status !== "GATE_PASSED"}
                          onClick={handlePrepareReview}
                        >
                          <UserRound aria-hidden="true" />
                          Prepare review
                        </Button>
                      </div>
                    </section>
                  </div>
                ) : (
                  <div className="empty-state">
                    <ClipboardCheck aria-hidden="true" className="size-8 text-primary" />
                    <h3 className="mt-4 text-xl font-semibold">One bounded package at a time</h3>
                    <p className="mt-2 max-w-md text-center text-sm leading-6 text-muted-foreground">
                      Define the actual deliverable and acceptance criteria at left. A browser agent can
                      perform the same action through WebMCP.
                    </p>
                  </div>
                )}
              </TabsContent>

              <TabsContent className="p-4 sm:p-5" value="evidence">
                <div className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
                  <section className="rounded-2xl border border-border bg-background/35 p-4">
                    <div className="mb-4 flex items-center gap-2">
                      <Plus aria-hidden="true" className="size-4 text-primary" />
                      <h3 className="font-semibold">Add evidence</h3>
                    </div>
                    <div className="space-y-3">
                      <label className="field-label" htmlFor="evidence-title">Evidence title</label>
                      <Input
                        id="evidence-title"
                        maxLength={120}
                        placeholder="Production smoke-test result"
                        value={evidenceTitle}
                        onChange={(event) => setEvidenceTitle(event.target.value)}
                      />
                      <label className="field-label" htmlFor="source-url">HTTPS source</label>
                      <Input
                        id="source-url"
                        maxLength={500}
                        placeholder="https://…"
                        type="url"
                        value={sourceUrl}
                        onChange={(event) => setSourceUrl(event.target.value)}
                      />
                      <label className="field-label" htmlFor="evidence-summary">What this proves</label>
                      <Textarea
                        id="evidence-summary"
                        maxLength={800}
                        placeholder="State the observed fact and its relevance."
                        rows={4}
                        value={summary}
                        onChange={(event) => setSummary(event.target.value)}
                      />
                      <label className="field-label" htmlFor="criterion-select">Criterion</label>
                      <Select value={activeCriterionId} onValueChange={setCriterionId}>
                        <SelectTrigger className="w-full" id="criterion-select">
                          <SelectValue placeholder="Select a criterion" />
                        </SelectTrigger>
                        <SelectContent>
                          {workspace.workItem?.criteria.map((criterion) => (
                            <SelectItem key={criterion.id} value={criterion.id}>
                              {criterion.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <label className="field-label" htmlFor="confidence-select">Confidence</label>
                      <Select value={confidence} onValueChange={(value) => setConfidence(value as Confidence)}>
                        <SelectTrigger className="w-full" id="confidence-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="HIGH">High</SelectItem>
                          <SelectItem value="MEDIUM">Medium</SelectItem>
                          <SelectItem value="LOW">Low — does not satisfy gate</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button className="w-full" disabled={!workspace.workItem} onClick={handleAddEvidence}>
                        <Database aria-hidden="true" />
                        Add to evidence plane
                      </Button>
                    </div>
                  </section>

                  <section className="min-w-0">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <h3 className="font-semibold">Evidence ledger</h3>
                      <Badge variant="outline">{workspace.evidence.length} item(s)</Badge>
                    </div>
                    <div className="overflow-hidden rounded-2xl border border-border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Evidence</TableHead>
                            <TableHead>Criterion</TableHead>
                            <TableHead>Confidence</TableHead>
                            <TableHead>Actor</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {workspace.evidence.length ? (
                            workspace.evidence.map((item) => (
                              <TableRow key={item.id}>
                                <TableCell className="max-w-[260px] whitespace-normal">
                                  <a
                                    className="font-medium text-primary hover:underline"
                                    href={item.sourceUrl}
                                    rel="noreferrer"
                                    target="_blank"
                                  >
                                    {item.title}
                                  </a>
                                  <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                                    {item.summary}
                                  </p>
                                </TableCell>
                                <TableCell className="max-w-[220px] whitespace-normal text-xs text-muted-foreground">
                                  {criterionById.get(item.criterionId) ?? "Unknown"}
                                </TableCell>
                                <TableCell><Badge variant="outline">{item.confidence}</Badge></TableCell>
                                <TableCell>{item.actor}</TableCell>
                              </TableRow>
                            ))
                          ) : (
                            <TableRow>
                              <TableCell className="h-28 text-center text-muted-foreground" colSpan={4}>
                                No evidence has been recorded.
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  </section>
                </div>
              </TabsContent>

              <TabsContent className="p-4 sm:p-5" value="audit">
                <div className="space-y-2">
                  {workspace.audit.map((event) => (
                    <article className="audit-row" key={event.id}>
                      <div className="mt-1 grid size-8 shrink-0 place-items-center rounded-lg bg-secondary text-secondary-foreground">
                        {event.actor === "AGENT" ? (
                          <Bot aria-hidden="true" className="size-4" />
                        ) : event.actor === "HUMAN" ? (
                          <UserRound aria-hidden="true" className="size-4" />
                        ) : (
                          <Activity aria-hidden="true" className="size-4" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-mono text-xs font-semibold tracking-wide text-primary">
                            {event.action}
                          </p>
                          <span className="text-xs text-muted-foreground">{event.actor}</span>
                        </div>
                        <p className="mt-1 text-sm leading-6">{event.detail}</p>
                        <time className="mt-1 block text-xs text-muted-foreground" dateTime={event.timestamp}>
                          {new Date(event.timestamp).toLocaleString()}
                        </time>
                      </div>
                    </article>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </div>

          <div aria-live="polite" className="notice-bar">
            <Activity aria-hidden="true" className="size-4 shrink-0 text-primary" />
            <p>{notice}</p>
          </div>
        </section>

        <aside className="space-y-4">
          <section className="surface-panel p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Control state</p>
                <h2 className="mt-1 text-lg font-semibold">Human release gate</h2>
              </div>
              <LockKeyhole aria-hidden="true" className="size-5 text-primary" />
            </div>
            <div className="mt-4 grid gap-2 text-sm">
              <div className="state-line">
                <span>Acceptance gate</span>
                <strong>{workspace.gate?.passed ? "PASS" : workspace.gate ? "FAIL" : "PENDING"}</strong>
              </div>
              <div className="state-line">
                <span>Release performed</span>
                <strong>{workspace.releasePerformed ? "TRUE" : "FALSE"}</strong>
              </div>
              <div className="state-line">
                <span>Current state</span>
                <strong className="text-right">{workspace.status}</strong>
              </div>
            </div>

            {workspace.status === "AWAITING_HUMAN_REVIEW" ? (
              <div className="mt-4 border-t border-border pt-4">
                <label className="field-label" htmlFor="review-note">Accountable review note</label>
                <Textarea
                  id="review-note"
                  maxLength={400}
                  placeholder="Record why this package is approved or returned."
                  rows={4}
                  value={reviewNote}
                  onChange={(event) => setReviewNote(event.target.value)}
                />
                <div className="mt-3 grid gap-2">
                  <Button onClick={() => handleHumanDecision("APPROVE")}>
                    <CheckCircle2 aria-hidden="true" />
                    Approve release
                  </Button>
                  <Button variant="outline" onClick={() => handleHumanDecision("REQUEST_REVISION")}>
                    <XCircle aria-hidden="true" />
                    Request revision
                  </Button>
                </div>
              </div>
            ) : (
              <div className="mt-4 rounded-xl border border-dashed border-border p-4 text-sm leading-6 text-muted-foreground">
                The approval controls appear only after a current passing gate queues this package for
                human review.
              </div>
            )}
          </section>

          <section className="surface-panel p-4">
            <p className="eyebrow">Shared control plane</p>
            <div className="mt-3 space-y-3">
              <div className="flow-step">
                <UserRound aria-hidden="true" />
                <span>Human defines intent and controls release</span>
              </div>
              <div className="flow-step">
                <Bot aria-hidden="true" />
                <span>Browser agent uses narrow WebMCP tools</span>
              </div>
              <div className="flow-step">
                <FileCheck2 aria-hidden="true" />
                <span>Deterministic gate verifies evidence coverage</span>
              </div>
              <div className="flow-step">
                <LinkIcon aria-hidden="true" />
                <span>One visible state, one auditable history</span>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </main>
  )
}
