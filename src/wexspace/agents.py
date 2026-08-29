"""Governed three-agent engineering workflow."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from .hydraulics import calculate_network, independently_verify, validate_network_input
from .security import policy_check
from .state import SQLiteStateStore, utc_now


def default_registry_path() -> Path:
    """Return the registry copy embedded in the installed Python package."""
    return Path(__file__).with_name("agent_registry.json")


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class AgentFleet:
    def __init__(self, store: SQLiteStateStore, registry_path: str | Path | None = None):
        self.store = store
        self.registry_path = Path(registry_path) if registry_path else default_registry_path()
        self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self._agent_ids = {agent["agent_id"] for agent in self.registry["agents"]}
        required = {
            "wexspace_governing_agent",
            "iew_engineering_specialist",
            "wexspace_verification_evidence_specialist",
        }
        if not required.issubset(self._agent_ids):
            raise ValueError("agent registry is missing required specialists")

    def start(
        self,
        goal: str,
        payload: dict[str, Any],
        *,
        pause_after: str | None = None,
        run_immediately: bool = True,
    ) -> dict[str, Any]:
        workflow_id = f"WFX-{uuid.uuid4().hex[:12].upper()}"
        self.store.create_workflow(workflow_id, goal, payload)
        self.store.add_event(
            workflow_id,
            "wexspace_governing_agent",
            "workflow_created",
            "QUEUED",
            {"goal": goal, "input_sha256": canonical_sha256(payload)},
        )
        if run_immediately:
            return self.resume(workflow_id, pause_after=pause_after)
        return self.status(workflow_id)

    def resume(self, workflow_id: str, *, pause_after: str | None = None) -> dict[str, Any]:
        workflow = self.store.get(workflow_id)
        if workflow["status"] in {"RELEASED", "BLOCKED_POLICY", "BLOCKED_MISSING_INPUT", "REJECTED_VERIFICATION"}:
            return self.status(workflow_id)
        if workflow["current_step"] == "GOVERNANCE":
            policy = policy_check(workflow["goal"], workflow["input"])
            errors = validate_network_input(workflow["input"])
            context_gate = policy["context_gate"]
            scope_gate = policy["scope_relevance_actionability"]
            self.store.add_event(
                workflow_id,
                "wexspace_governing_agent",
                "context_allowlist_decision",
                "PASS" if context_gate["allowed"] else "BLOCK",
                context_gate,
            )
            self.store.add_event(
                workflow_id,
                "wexspace_governing_agent",
                "scope_relevance_actionability_gate",
                "PASS" if scope_gate["allowed"] else "BLOCK",
                scope_gate,
            )
            self.store.add_event(
                workflow_id,
                "wexspace_governing_agent",
                "policy_decision",
                "PASS" if policy["allowed"] else "BLOCK",
                policy,
            )
            if not policy["allowed"]:
                self.store.update(
                    workflow_id,
                    status="BLOCKED_POLICY",
                    current_step="TERMINAL",
                    evidence_json={"policy": policy, "validation_errors": errors},
                )
                return self.status(workflow_id)
            if errors:
                self.store.add_event(
                    workflow_id,
                    "wexspace_governing_agent",
                    "missing_input_control",
                    "BLOCK",
                    {"errors": errors},
                )
                self.store.update(
                    workflow_id,
                    status="BLOCKED_MISSING_INPUT",
                    current_step="TERMINAL",
                    evidence_json={"policy": policy, "validation_errors": errors},
                )
                return self.status(workflow_id)
            self.store.add_event(
                workflow_id,
                "wexspace_governing_agent",
                "delegation",
                "ROUTED",
                {
                    "to_agent": "iew_engineering_specialist",
                    "task": "deterministic hydraulic calculation",
                    "tool": "calculate_network",
                },
            )
            self.store.update(workflow_id, status="RUNNING", current_step="ENGINEERING")
            workflow = self.store.get(workflow_id)

        if workflow["current_step"] == "ENGINEERING":
            calculation = calculate_network(workflow["input"])
            self.store.add_event(
                workflow_id,
                "iew_engineering_specialist",
                "deterministic_tool_call",
                "PASS",
                {
                    "tool": "calculate_network",
                    "method": calculation["method"],
                    "result_sha256": canonical_sha256(calculation),
                    "accepted": calculation["accepted"],
                },
            )
            self.store.update(
                workflow_id,
                status="RUNNING",
                current_step="VERIFICATION",
                result_json=calculation,
            )
            if pause_after == "engineering":
                self.store.update(workflow_id, status="PAUSED", current_step="VERIFICATION")
                self.store.add_event(
                    workflow_id,
                    "wexspace_governing_agent",
                    "state_transition",
                    "PAUSED",
                    {"resume_from": "VERIFICATION"},
                )
                return self.status(workflow_id)
            workflow = self.store.get(workflow_id)

        if workflow["current_step"] == "VERIFICATION":
            self.store.add_event(
                workflow_id,
                "wexspace_governing_agent",
                "delegation",
                "ROUTED",
                {
                    "to_agent": "wexspace_verification_evidence_specialist",
                    "task": "independent recalculation and evidence packaging",
                },
            )
            verification = independently_verify(workflow["input"], workflow["result"])
            evidence = {
                "workflow_id": workflow_id,
                "generated_at": utc_now(),
                "input_sha256": canonical_sha256(workflow["input"]),
                "calculation_sha256": canonical_sha256(workflow["result"]),
                "verification_sha256": canonical_sha256(verification),
                "agent_registry_sha256": hashlib.sha256(self.registry_path.read_bytes()).hexdigest(),
                "provenance_chain": [
                    "synthetic_input",
                    "competition_context_allowlist",
                    "scope_relevance_actionability_gate",
                    "governing_policy",
                    "wexspace_governing_agent",
                    "iew_engineering_specialist",
                    "deterministic_calculation",
                    "wexspace_verification_evidence_specialist",
                    "independent_recalculation",
                    "human_review_gate",
                ],
                "human_release_required": True,
            }
            self.store.add_event(
                workflow_id,
                "wexspace_verification_evidence_specialist",
                "independent_validation",
                "PASS" if verification["verified"] else "FAIL",
                {
                    "verification_sha256": evidence["verification_sha256"],
                    "checks": verification["checks"],
                },
            )
            if not verification["verified"]:
                self.store.update(
                    workflow_id,
                    status="REJECTED_VERIFICATION",
                    current_step="TERMINAL",
                    verification_json=verification,
                    evidence_json=evidence,
                )
                return self.status(workflow_id)
            self.store.update(
                workflow_id,
                status="AWAITING_HUMAN_REVIEW",
                current_step="HUMAN_REVIEW",
                verification_json=verification,
                evidence_json=evidence,
            )
            self.store.add_event(
                workflow_id,
                "wexspace_governing_agent",
                "human_review_gate",
                "WAITING",
                {"consequential_transition": "release verified engineering result"},
            )
        return self.status(workflow_id)

    def approve(self, workflow_id: str, reviewer: str) -> dict[str, Any]:
        workflow = self.store.get(workflow_id)
        if workflow["status"] != "AWAITING_HUMAN_REVIEW":
            raise ValueError("workflow is not awaiting human review")
        reviewer = reviewer.strip()
        if not reviewer:
            raise ValueError("reviewer identity is required")
        review = {
            "decision": "APPROVED",
            "reviewer": reviewer,
            "reviewed_at": utc_now(),
            "statement": "Human reviewer approved release of the verified synthetic demonstration result.",
        }
        self.store.update(
            workflow_id,
            status="RELEASED",
            current_step="TERMINAL",
            review_json=review,
        )
        self.store.add_event(
            workflow_id,
            "wexspace_governing_agent",
            "human_review_gate",
            "APPROVED",
            {"reviewer": reviewer},
        )
        return self.status(workflow_id)

    def worker_once(self) -> dict[str, Any] | None:
        queued = self.store.list_by_status(("QUEUED", "PAUSED"))
        if not queued:
            return None
        return self.resume(queued[0]["workflow_id"])

    def status(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.store.get(workflow_id)
        workflow["events"] = self.store.events(workflow_id)
        return workflow
