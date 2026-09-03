import assert from "node:assert/strict";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

import { createServer } from "vite";

const root = fileURLToPath(new URL("..", import.meta.url));
const vite = await createServer({
  appType: "custom",
  configFile: false,
  root,
  resolve: { alias: { "@": root } },
  server: { middlewareMode: true },
});

after(async () => {
  await vite.close();
});

async function modules() {
  const domain = await vite.ssrLoadModule("/lib/proofdesk/domain.ts");
  const webmcp = await vite.ssrLoadModule("/lib/proofdesk/webmcp.ts");
  return { domain, webmcp };
}

function createCase(domain) {
  return domain.createWorkItem(
    domain.createInitialState(),
    {
      title: "Release evidence package",
      objective: "Prove that a bounded public release is functional and reviewable.",
      primaryDeliverable: "Verified release package",
      criteria: ["Endpoint works", "Documentation exists", "Secret scan passes"],
    },
    "HUMAN",
  );
}

test("deterministic gate requires non-low evidence for every criterion", async () => {
  const { domain } = await modules();
  let state = createCase(domain);

  for (const [index, criterion] of state.workItem.criteria.entries()) {
    state = domain.addEvidence(
      state,
      {
        title: `Evidence ${index + 1}`,
        sourceUrl: `https://example.com/evidence/${index + 1}`,
        summary: `This independently observed result covers criterion ${index + 1} with a reproducible source.`,
        criterionId: criterion.id,
        confidence: index === 2 ? "LOW" : "HIGH",
      },
      "HUMAN",
    );
  }

  state = domain.runAcceptanceGate(state, "HUMAN");
  assert.equal(state.gate.passed, false);
  assert.equal(state.gate.score, 67);
  assert.equal(state.status, "GATE_FAILED");
});

test("passing package stops at human review until a human decision", async () => {
  const { domain } = await modules();
  let state = createCase(domain);

  for (const [index, criterion] of state.workItem.criteria.entries()) {
    state = domain.addEvidence(
      state,
      {
        title: `Qualified evidence ${index + 1}`,
        sourceUrl: `https://example.com/qualified/${index + 1}`,
        summary: `A concrete, reproducible observation satisfies required criterion ${index + 1}.`,
        criterionId: criterion.id,
        confidence: "HIGH",
      },
      "AGENT",
    );
  }

  state = domain.runAcceptanceGate(state, "AGENT");
  assert.equal(state.gate.passed, true);
  assert.equal(state.status, "GATE_PASSED");

  state = domain.prepareHumanReview(state, "AGENT");
  assert.equal(state.status, "AWAITING_HUMAN_REVIEW");
  assert.equal(state.releasePerformed, false);

  state = domain.recordHumanDecision(
    state,
    "APPROVE",
    "Reviewed the evidence package and approved the bounded release.",
  );
  assert.equal(state.status, "RELEASED");
  assert.equal(state.releasePerformed, true);
  assert.equal(state.audit[0].actor, "HUMAN");
});

test("WebMCP registers five scoped tools and exposes no release tool", async () => {
  const { domain, webmcp } = await modules();
  let state = domain.createInitialState();
  const registered = [];
  const fakeContext = {
    registerTool(tool) {
      registered.push(tool);
    },
  };
  const runtime = {
    getState: () => state,
    commit(operation) {
      state = operation(state);
      return state;
    },
  };

  const result = await webmcp.registerProofDeskTools(fakeContext, runtime);
  assert.equal(result.status, "AVAILABLE");
  assert.equal(result.toolCount, 5);
  assert.deepEqual(
    registered.map((tool) => tool.name),
    [
      "wexspace.inspect_workspace",
      "wexspace.create_work_item",
      "wexspace.add_evidence",
      "wexspace.run_acceptance_gate",
      "wexspace.prepare_human_review",
    ],
  );
  assert.equal(registered.some((tool) => /release|approve/i.test(tool.name)), false);
  assert.equal(registered[0].annotations.readOnlyHint, true);
  assert.equal(registered.slice(1).every((tool) => tool.annotations.readOnlyHint === false), true);
  assert.equal(registered.every((tool) => tool.inputSchema.additionalProperties === false), true);

  const createTool = registered.find((tool) => tool.name === "wexspace.create_work_item");
  const response = await createTool.execute({
    title: "Agent-created package",
    objective: "Create a bounded package through the actual WebMCP execution path.",
    primaryDeliverable: "Auditable evidence package",
    criteria: ["One source is present", "Gate result is visible"],
  });
  assert.equal(response.ok, true);
  assert.equal(state.audit[0].actor, "AGENT");
  assert.equal(state.status, "IN_PROGRESS");
});

test("WebMCP absence leaves a truthful unavailable state", async () => {
  const { domain, webmcp } = await modules();
  const state = domain.createInitialState();
  const result = await webmcp.registerProofDeskTools(undefined, {
    getState: () => state,
    commit: () => state,
  });
  assert.deepEqual(result.status, "UNAVAILABLE");
  assert.match(result.reason, /document\.modelContext/);
});
