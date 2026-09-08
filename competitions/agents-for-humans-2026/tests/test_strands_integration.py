"""New integration boundary only. Does not rerun or replace the five R01 kernel tests."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

import pytest
from strands import Agent

from scripted_model import ScriptedModel
from wexspace_professional_agent.core import WorkRequest
from wexspace_professional_agent.durable import IntegrityError, WorkRepository, digest
from wexspace_professional_agent.strands_adapter import (
    ProviderAuthRequired, RunTrace, build_agent, gemini_model, invocation_lock, run_workflow,
)
from wexspace_professional_agent.workflow import ProfessionalWorkflow

CAPSULE = Path(__file__).resolve().parents[1]


@pytest.fixture
def setup_work(tmp_path):
    inputs = tmp_path / "inputs"
    shutil.copytree(CAPSULE / "examples", inputs)
    repo = WorkRepository(tmp_path / "work.sqlite3")
    request = WorkRequest("test-001", "Receiving review", "Reconcile receiving records for human review",
                          ("orders_csv", "deliveries_csv", "reviewer"),
                          {"orders_csv": "orders.csv", "deliveries_csv": "deliveries.csv", "reviewer": "demo-operator"},
                          ("reconciliation.json", "review.md"))
    repo.register(request)
    return repo, request, inputs, tmp_path


def wf(setup):
    repo, request, inputs, _ = setup
    return ProfessionalWorkflow(repo, request.work_id, inputs)


def test_real_strands_tool_loop_evidence_and_session_restore(setup_work, record_property):
    workflow = wf(setup_work)
    root = setup_work[3] / "agent"
    model = ScriptedModel(["inspect_request", "reconcile_delivery", "prepare_review_package"])
    result = asyncio.run(run_workflow(workflow, root, model=model))
    assert result["model_origin"] == "injected_test_model"
    assert result["provider_invoked"] is False
    assert result["work"]["state"] == "HUMAN_REVIEW"
    assert model.calls == 4
    exported = workflow.repo.export(workflow.work_id, setup_work[3] / "export")
    comparison = json.loads((exported / "reconciliation.json").read_bytes())
    assert comparison["discrepancy_count"] == 2
    assert [line["difference"] for line in comparison["lines"]] == ["-2", "0.0", "1"]
    for name, sha in comparison["source_hashes"].items():
        assert digest((exported / name).read_bytes()) == sha
    directory = root / workflow.work_id
    restored = build_agent(workflow, ScriptedModel(), directory / "sessions", RunTrace(directory / "traces", "restore-inspection"))
    assert isinstance(restored, Agent)
    assert len(restored.messages) >= 8
    assert set(restored.tool_names) == {"inspect_request", "reconcile_delivery", "prepare_review_package"}
    assert not any("approv" in name or "decid" in name for name in restored.tool_names)
    trace = [json.loads(line) for line in (directory / "traces" / f"{result['execution_id']}.jsonl").read_text().splitlines()]
    assert [e["tool"] for e in trace if e["event"] == "tool_completed"] == ["inspect_request", "reconcile_delivery", "prepare_review_package"]
    assert all(e["execution_id"] == result["execution_id"] for e in trace)
    record_property("scenario", "real-sdk-test-model-receiving-reconciliation")
    record_property("latency_ms", result["elapsed_ms"])
    record_property("evidence_verified", len(result["work"]["evidence"]))
    record_property("provider_requests", 0)


@pytest.mark.parametrize("field", ["orders_csv", "deliveries_csv", "reviewer"])
def test_missing_input_stops_before_model_and_accepts_only_missing_fact(setup_work, field, record_property):
    repo, request, inputs, root = setup_work
    req = replace(request, work_id=f"missing-{field}", inputs={k: v for k, v in request.inputs.items() if k != field})
    repo.register(req)
    workflow = ProfessionalWorkflow(repo, req.work_id, inputs)
    model = ScriptedModel(["reconcile_delivery"])
    result = asyncio.run(run_workflow(workflow, root / "agent", model=model))
    assert result["work"]["missing_inputs"] == [field]
    assert result["work"]["state"] == "NEEDS_INPUT"
    assert model.calls == 0
    before = repo.status(req.work_id)
    asyncio.run(run_workflow(workflow, root / "agent", model=model))
    assert repo.status(req.work_id) == before
    with pytest.raises(ValueError):
        workflow.provide_inputs({"objective": "replace a completed field"})
    workflow.provide_inputs({field: request.inputs[field]})
    assert workflow.inspect_request()["missing"] == []
    record_property("missing_field_detected", field)


def test_abrupt_process_exit_restores_exact_cursor_without_redoing_work(setup_work, record_property):
    repo, request, inputs, root = setup_work
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(CAPSULE / "src"), str(CAPSULE / "tests")])}
    child = '''import asyncio,sys
from pathlib import Path
from scripted_model import ScriptedModel
from wexspace_professional_agent.durable import WorkRepository
from wexspace_professional_agent.workflow import ProfessionalWorkflow
from wexspace_professional_agent.strands_adapter import run_workflow
root=Path(sys.argv[1])
w=ProfessionalWorkflow(WorkRepository(root/'work.sqlite3'),'test-001',root/'inputs')
asyncio.run(run_workflow(w,root/'agent',model=ScriptedModel(['inspect_request','reconcile_delivery','CRASH'])))
'''
    child_result = subprocess.run([sys.executable, "-c", child, str(root)], env=env, capture_output=True, timeout=40)
    assert child_result.returncode == 23, child_result.stderr.decode()
    before = repo.status(request.work_id)
    assert before["state"] == "IN_PROGRESS"
    assert len(before["evidence"]) == 3
    fresh = WorkRepository(repo.path)
    assert fresh.status(request.work_id) == before
    workflow = ProfessionalWorkflow(fresh, request.work_id, inputs)
    # Remove original inputs: recovery must use committed bytes, not re-read or redo them.
    (inputs / "orders.csv").unlink()
    (inputs / "deliveries.csv").unlink()
    assert workflow.reconcile_delivery()["reused"] is True
    assert fresh.status(request.work_id) == before
    resumed = asyncio.run(run_workflow(workflow, root / "agent", model=ScriptedModel(["reconcile_delivery", "prepare_review_package"])))
    assert resumed["work"]["state"] == "HUMAN_REVIEW"
    assert resumed["work"]["evidence"][:3] == before["evidence"]
    assert resumed["work"]["last_applied_sequence"] == before["last_applied_sequence"] + 2
    record_property("resume_cursor_before", before["last_applied_sequence"])
    record_property("resume_cursor_after", resumed["work"]["last_applied_sequence"])
    record_property("preserved_evidence", 3)
    record_property("duplicate_reconciliation_events", 0)


def test_concurrent_duplicate_tool_calls_commit_once(setup_work):
    workflow = wf(setup_work)
    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(lambda _: workflow.reconcile_delivery(), range(2)))
    assert sorted(v["reused"] for v in values) == [False, True]
    assert values[0]["evidence"] == values[1]["evidence"]
    assert len(workflow.repo.status(workflow.work_id)["evidence"]) == 3
    with invocation_lock(setup_work[3] / "locked"):
        with pytest.raises(RuntimeError):
            with invocation_lock(setup_work[3] / "locked"):
                pytest.fail("A second session writer entered")


@pytest.mark.parametrize("approve", [True, False])
def test_human_gate_is_required_and_final_decision_is_idempotent(setup_work, approve):
    workflow = wf(setup_work)
    with pytest.raises(ValueError):
        workflow.decide(approve=approve, reviewer="demo-operator")
    workflow.reconcile_delivery()
    with pytest.raises(ValueError):
        workflow.decide(approve=approve, reviewer="demo-operator")
    workflow.prepare_review_package()
    with pytest.raises(PermissionError):
        workflow.decide(approve=approve, reviewer="unconfigured-reviewer")
    model = ScriptedModel(["reconcile_delivery"])
    asyncio.run(run_workflow(workflow, setup_work[3] / "agent", model=model))
    assert model.calls == 0
    result = workflow.decide(approve=approve, reviewer="demo-operator")
    state = workflow.repo.status(workflow.work_id)
    assert state["state"] == ("COMPLETED" if approve else "FAILED")
    assert workflow.decide(approve=approve, reviewer="demo-operator") == result
    assert workflow.repo.status(workflow.work_id) == state
    with pytest.raises(ValueError):
        workflow.decide(approve=not approve, reviewer="demo-operator")
    if approve:
        target = workflow.repo.export(workflow.work_id, setup_work[3] / "export")
        manifest = json.loads((target / "release-manifest.json").read_bytes())
        assert manifest["approved"] is True
        assert all(digest((target / ref["artifact_id"]).read_bytes()) == ref["sha256"] for ref in manifest["artifacts"])


@pytest.mark.parametrize("invalid", ["duplicate", "precision", "markup", "headers"])
def test_invalid_csv_cannot_commit_partial_work(setup_work, invalid):
    workflow = wf(setup_work)
    source = setup_work[2] / "deliveries.csv"
    values = {
        "duplicate": "receipt_id,line_id,quantity\nR1,L1,1\nR1,L1,2\n",
        "precision": "receipt_id,line_id,quantity\nR1,L1,0.0000001\n",
        "markup": "receipt_id,line_id,quantity\nR1,<script>,1\n",
        "headers": "receipt_id,line_id,quantity,quantity\nR1,L1,1,2\n",
    }
    source.write_text(values[invalid])
    before = workflow.repo.status(workflow.work_id)
    with pytest.raises(ValueError):
        workflow.reconcile_delivery()
    assert workflow.repo.status(workflow.work_id) == before


def test_input_path_escape_is_rejected(setup_work):
    repo, request, inputs, root = setup_work
    outside = root / "outside.csv"
    outside.write_text("line_id,item,quantity\nX,private,1\n")
    req = replace(request, work_id="escape-test", inputs={**request.inputs, "orders_csv": "../outside.csv"})
    repo.register(req)
    with pytest.raises(ValueError, match="authorized"):
        ProfessionalWorkflow(repo, req.work_id, inputs).reconcile_delivery()
    assert repo.status(req.work_id)["state"] == "RECEIVED"


@pytest.mark.parametrize("layer", ["artifact", "event"])
def test_tampering_blocks_recovery_and_human_release(setup_work, layer):
    workflow = wf(setup_work)
    workflow.reconcile_delivery()
    workflow.prepare_review_package()
    with sqlite3.connect(workflow.repo.path) as db:
        if layer == "artifact":
            db.execute("UPDATE artifacts SET payload=? WHERE name='reconciliation.json'", (b"{}",))
        else:
            db.execute("UPDATE events SET body=? WHERE sequence=2", (b"{}",))
    with pytest.raises(IntegrityError):
        workflow.repo.status(workflow.work_id)
    with pytest.raises(IntegrityError):
        workflow.decide(approve=True, reviewer="demo-operator")


def test_missing_provider_auth_fails_closed_and_preserves_work(setup_work, monkeypatch):
    for key in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "WEXSPACE_GEMINI_VERTEX_PROJECT"):
        monkeypatch.delenv(key, raising=False)
    workflow = wf(setup_work)
    before = workflow.repo.status(workflow.work_id)
    with pytest.raises(ProviderAuthRequired):
        asyncio.run(run_workflow(workflow, setup_work[3] / "agent"))
    assert workflow.repo.status(workflow.work_id) == before


def test_early_model_stop_cannot_invent_work_completion(setup_work):
    workflow = wf(setup_work)
    result = asyncio.run(run_workflow(workflow, setup_work[3] / "agent", model=ScriptedModel()))
    assert result["work"]["state"] == "RECEIVED"
    assert result["work"]["evidence"] == []
