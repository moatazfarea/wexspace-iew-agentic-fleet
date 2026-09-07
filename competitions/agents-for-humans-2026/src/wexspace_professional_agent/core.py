from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Tuple
import hashlib
import json


class WorkState(str, Enum):
    RECEIVED = "RECEIVED"
    NEEDS_INPUT = "NEEDS_INPUT"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EventKind(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    MISSING_INPUTS_DETECTED = "MISSING_INPUTS_DETECTED"
    PLAN_CREATED = "PLAN_CREATED"
    WORK_STARTED = "WORK_STARTED"
    ARTIFACT_RECORDED = "ARTIFACT_RECORDED"
    HUMAN_REVIEW_REQUESTED = "HUMAN_REVIEW_REQUESTED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"
    WORK_COMPLETED = "WORK_COMPLETED"
    WORK_FAILED = "WORK_FAILED"


class DuplicateEventError(ValueError):
    pass


class InvalidEventSequence(ValueError):
    pass


class InvalidTransition(ValueError):
    pass


@dataclass(frozen=True)
class WorkRequest:
    work_id: str
    title: str
    objective: str
    required_fields: Tuple[str, ...] = ()
    inputs: Mapping[str, Any] = field(default_factory=dict)
    required_deliverables: Tuple[str, ...] = ()

    def missing_inputs(self) -> Tuple[str, ...]:
        missing = []
        for key in self.required_fields:
            value = self.inputs.get(key)
            if value is None or value == "" or value == [] or value == {}:
                missing.append(key)
        return tuple(missing)


@dataclass(frozen=True)
class EvidenceRef:
    artifact_id: str
    sha256: str
    media_type: str
    description: str = ""

    @staticmethod
    def from_bytes(artifact_id: str, payload: bytes, media_type: str, description: str = "") -> "EvidenceRef":
        return EvidenceRef(
            artifact_id=artifact_id,
            sha256=hashlib.sha256(payload).hexdigest(),
            media_type=media_type,
            description=description,
        )


@dataclass(frozen=True)
class Event:
    event_id: str
    work_id: str
    sequence: int
    kind: EventKind
    payload: Mapping[str, Any] = field(default_factory=dict)
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def canonical_json(self) -> str:
        body = {
            "event_id": self.event_id,
            "work_id": self.work_id,
            "sequence": self.sequence,
            "kind": self.kind.value,
            "payload": dict(self.payload),
            "occurred_at": self.occurred_at,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class RebuiltWork:
    work_id: str
    state: WorkState
    cursor: int
    missing_inputs: Tuple[str, ...]
    plan: Tuple[str, ...]
    evidence: Tuple[EvidenceRef, ...]
    human_review_reason: Optional[str]
    completion_summary: Optional[str]
    rejected_reason: Optional[str]

    @property
    def resume_pointer(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "last_applied_sequence": self.cursor,
            "next_expected_sequence": self.cursor + 1,
            "state": self.state.value,
        }


class EventStore:
    """Append-only in-memory event store with deterministic rebuild semantics."""

    def __init__(self) -> None:
        self._events: List[Event] = []
        self._event_ids: set[str] = set()

    def append(self, event: Event) -> None:
        if event.event_id in self._event_ids:
            raise DuplicateEventError(event.event_id)

        work_events = [e for e in self._events if e.work_id == event.work_id]
        expected = (work_events[-1].sequence + 1) if work_events else 1
        if event.sequence != expected:
            raise InvalidEventSequence(
                f"work_id={event.work_id}: expected sequence {expected}, got {event.sequence}"
            )

        self._events.append(event)
        self._event_ids.add(event.event_id)

    def events_for(self, work_id: str) -> Tuple[Event, ...]:
        return tuple(e for e in self._events if e.work_id == work_id)

    def rebuild(self, work_id: str) -> RebuiltWork:
        events = self.events_for(work_id)
        if not events:
            raise KeyError(work_id)

        state = WorkState.RECEIVED
        cursor = 0
        missing_inputs: Tuple[str, ...] = ()
        plan: Tuple[str, ...] = ()
        evidence: List[EvidenceRef] = []
        human_review_reason: Optional[str] = None
        completion_summary: Optional[str] = None
        rejected_reason: Optional[str] = None

        for event in events:
            cursor = event.sequence
            p = dict(event.payload)

            if event.kind == EventKind.REQUEST_RECEIVED:
                if event.sequence != 1:
                    raise InvalidTransition("REQUEST_RECEIVED must be first")
                state = WorkState.RECEIVED

            elif event.kind == EventKind.MISSING_INPUTS_DETECTED:
                missing_inputs = tuple(p.get("fields", ()))
                state = WorkState.NEEDS_INPUT if missing_inputs else WorkState.RECEIVED

            elif event.kind == EventKind.PLAN_CREATED:
                plan = tuple(p.get("steps", ()))
                if not plan:
                    raise InvalidTransition("PLAN_CREATED requires at least one step")
                missing_inputs = ()
                state = WorkState.PLANNED

            elif event.kind == EventKind.WORK_STARTED:
                if state not in {WorkState.PLANNED, WorkState.IN_PROGRESS}:
                    raise InvalidTransition(f"WORK_STARTED not allowed from {state.value}")
                state = WorkState.IN_PROGRESS

            elif event.kind == EventKind.ARTIFACT_RECORDED:
                if state not in {WorkState.IN_PROGRESS, WorkState.HUMAN_REVIEW}:
                    raise InvalidTransition(f"ARTIFACT_RECORDED not allowed from {state.value}")
                evidence.append(
                    EvidenceRef(
                        artifact_id=str(p["artifact_id"]),
                        sha256=str(p["sha256"]),
                        media_type=str(p["media_type"]),
                        description=str(p.get("description", "")),
                    )
                )

            elif event.kind == EventKind.HUMAN_REVIEW_REQUESTED:
                if state != WorkState.IN_PROGRESS:
                    raise InvalidTransition(f"HUMAN_REVIEW_REQUESTED not allowed from {state.value}")
                human_review_reason = str(p.get("reason", ""))
                state = WorkState.HUMAN_REVIEW

            elif event.kind == EventKind.HUMAN_APPROVED:
                if state != WorkState.HUMAN_REVIEW:
                    raise InvalidTransition("HUMAN_APPROVED requires HUMAN_REVIEW")
                human_review_reason = None
                rejected_reason = None
                state = WorkState.IN_PROGRESS

            elif event.kind == EventKind.HUMAN_REJECTED:
                if state != WorkState.HUMAN_REVIEW:
                    raise InvalidTransition("HUMAN_REJECTED requires HUMAN_REVIEW")
                rejected_reason = str(p.get("reason", ""))
                state = WorkState.FAILED

            elif event.kind == EventKind.WORK_COMPLETED:
                if state != WorkState.IN_PROGRESS:
                    raise InvalidTransition("WORK_COMPLETED requires IN_PROGRESS")
                completion_summary = str(p.get("summary", ""))
                state = WorkState.COMPLETED

            elif event.kind == EventKind.WORK_FAILED:
                rejected_reason = str(p.get("reason", ""))
                state = WorkState.FAILED

            else:
                raise InvalidTransition(f"Unsupported event kind: {event.kind}")

        return RebuiltWork(
            work_id=work_id,
            state=state,
            cursor=cursor,
            missing_inputs=missing_inputs,
            plan=plan,
            evidence=tuple(evidence),
            human_review_reason=human_review_reason,
            completion_summary=completion_summary,
            rejected_reason=rejected_reason,
        )
