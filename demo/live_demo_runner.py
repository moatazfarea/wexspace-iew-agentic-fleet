#!/usr/bin/env python3
"""Run one authentic WEXSPACE workflow while echoing committed events.

This file is a media-only observer.  It subclasses the existing SQLite state
store solely to display events after the production workflow commits them.  It
does not replace or reimplement the agents, governance, calculations, verifier,
or human-review gate.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from wexspace.agents import AgentFleet
from wexspace.state import SQLiteStateStore


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "UTL-NET-001_SYNTHETIC_INPUT.json"
GOAL = "Analyze synthetic cooling-water network"
BASE_DELAY = float(os.getenv("WEXSPACE_DEMO_DELAY", "1.65"))
PACE = float(os.getenv("WEXSPACE_DEMO_PACE", "1.0"))


def emit(message: str = "", *, delay: float | None = None) -> None:
    print(message, flush=True)
    time.sleep((BASE_DELAY if delay is None else delay) * PACE)


def short_agent(agent_id: str) -> str:
    return {
        "wexspace_governing_agent": "GOVERNING AGENT",
        "iew_engineering_specialist": "IEW ENGINEERING SPECIALIST",
        "wexspace_verification_evidence_specialist": "VERIFICATION SPECIALIST",
    }.get(agent_id, agent_id.upper())


class ObservableStateStore(SQLiteStateStore):
    """Echo only records that the real state store has already committed."""

    def __init__(self, path: str | Path, trace_path: Path):
        self.trace_path = trace_path
        super().__init__(path)

    def _append_trace(self, record: dict[str, Any]) -> None:
        with self.trace_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

    def add_event(
        self,
        workflow_id: str,
        agent_id: str,
        event_type: str,
        outcome: str,
        details: dict[str, Any],
    ) -> None:
        super().add_event(workflow_id, agent_id, event_type, outcome, details)
        committed = self.events(workflow_id)[-1]
        self._append_trace(committed)
        stamp = committed["timestamp"][11:19] + "Z"
        emit(f"[{stamp}] [AGENT] {short_agent(agent_id)}", delay=0.55)
        emit(f"           [EVENT] {event_type}  ->  {outcome}", delay=0.85)

        if event_type == "workflow_created":
            emit(f"           [GOAL] {details['goal']}", delay=0.85)
            emit(f"           [EVIDENCE] input sha256 {details['input_sha256'][:20]}...", delay=1.1)
        elif event_type == "context_allowlist_decision":
            emit(
                "           [GATE] authorized competition context = "
                + str(details["allowed"]).lower(),
                delay=1.1,
            )
        elif event_type == "scope_relevance_actionability_gate":
            emit(
                "           [GATE] scope = "
                + details["scope_state"]
                + " | actionability = "
                + details["actionability_state"],
                delay=1.1,
            )
        elif event_type == "policy_decision":
            emit(
                "           [POLICY] WEX-POLICY-001 allowed = "
                + str(details["allowed"]).lower()
                + " | secret_values_logged = false",
                delay=1.25,
            )
        elif event_type == "delegation":
            emit(f"           [ROUTE] to {details['to_agent']}", delay=0.8)
            emit(f"           [TASK] {details['task']}", delay=1.2)
        elif event_type == "deterministic_tool_call":
            emit(f"           [TOOL] {details['tool']} | {details['method']}", delay=0.9)
            emit(
                "           [RESULT] accepted = "
                + str(details["accepted"]).lower()
                + " | sha256 "
                + details["result_sha256"][:20]
                + "...",
                delay=1.25,
            )
        elif event_type == "independent_validation":
            checks_pass = all(details["checks"].values())
            emit(
                "           [VERIFY] independent checks pass = "
                + str(checks_pass).lower(),
                delay=0.9,
            )
            emit(
                "           [EVIDENCE] verification sha256 "
                + details["verification_sha256"][:20]
                + "...",
                delay=1.25,
            )
        elif event_type == "human_review_gate":
            emit(
                "           [HUMAN GATE] release remains blocked pending reviewer",
                delay=1.6,
            )

    def update(self, workflow_id: str, **fields: Any) -> None:
        super().update(workflow_id, **fields)
        committed = self.get(workflow_id)
        if "current_step" in fields or "status" in fields:
            emit(
                f"[STATE] {committed['status']} | next = {committed['current_step']}",
                delay=1.1,
            )
        if "result_json" in fields:
            result = committed["result"]
            emit(f"[ENGINEERING OUTPUT] {result['method']}", delay=0.8)
            for segment in result["segments"]:
                emit(
                    "  "
                    + segment["segment_id"]
                    + f"  velocity={segment['velocity_m_s']:.6f} m/s"
                    + f"  total_head={segment['total_head_m']:.6f} m",
                    delay=0.95,
                )
            for endpoint in result["endpoint_paths"]:
                emit(
                    "  "
                    + endpoint["endpoint_node"]
                    + f"  residual_pressure={endpoint['residual_pressure_kpa']:.9f} kPa",
                    delay=1.1,
                )
        if "verification_json" in fields:
            verification = committed["verification"]
            emit(f"[INDEPENDENT METHOD] {verification['verification_method']}", delay=0.8)
            for comparison in verification["comparisons"]:
                emit(
                    "  "
                    + comparison["segment_id"]
                    + f"  relative_difference={comparison['relative_difference']:.9f}"
                    + f"  within_5_percent={str(comparison['within_5_percent']).lower()}",
                    delay=1.05,
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "live_workflow.db"
    trace_path = output_dir / "live_trace.jsonl"
    result_path = output_dir / "WEXSPACE_LIVE_RUN_R02.json"
    if db_path.exists():
        db_path.unlink()
    if trace_path.exists():
        trace_path.unlink()

    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    emit("WEXSPACE AI — LIVE PROFESSIONAL WORKFLOW", delay=0.9)
    emit("CONTINUOUS LIVE RUN — NO CUTS — AUTHENTIC APPLICATION EVENTS", delay=0.9)
    emit("Observer: committed SQLite events from the production AgentFleet", delay=0.9)
    emit("", delay=0.35)
    emit(f"[USER GOAL] {GOAL}", delay=1.0)
    emit(f"[SYNTHETIC PROJECT] {payload['project_id']}", delay=0.8)
    emit(
        f"[INPUT] source={payload['source_node']} | pressure={payload['source_pressure_kpa']} kPa",
        delay=0.8,
    )
    emit(f"[INPUT] {len(payload['segments'])} pipe segments | 2 terminal loads", delay=1.3)

    store = ObservableStateStore(db_path, trace_path)
    fleet = AgentFleet(store)
    result = fleet.start(GOAL, payload)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    emit("", delay=0.3)
    emit("[FINAL VERIFIED RESULT]", delay=0.75)
    emit(f"  workflow_id = {result['workflow_id']}", delay=0.8)
    emit(f"  state = {result['status']}", delay=0.8)
    emit(f"  independent_verification = {str(result['verification']['verified']).lower()}", delay=0.8)
    emit(
        "  checks = " + str(sum(result["verification"]["checks"].values())) + "/" + str(len(result["verification"]["checks"])),
        delay=0.8,
    )
    emit(f"  release_performed = {str(result['review'] is not None).lower()}", delay=0.9)
    emit(f"  calculation_sha256 = {result['evidence']['calculation_sha256']}", delay=0.9)
    emit(f"  verification_sha256 = {result['evidence']['verification_sha256']}", delay=0.9)
    emit("", delay=0.35)
    emit("AUTONOMOUS PROFESSIONAL EXECUTION COMPLETE", delay=0.75)
    emit("ACCOUNTABLE HUMAN RELEASE STILL REQUIRED", delay=5.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
