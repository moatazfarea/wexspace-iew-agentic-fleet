import unittest

from wexspace_professional_agent.core import (
    DuplicateEventError,
    Event,
    EventKind,
    EventStore,
    EvidenceRef,
    InvalidTransition,
    WorkRequest,
    WorkState,
)


class TestWorkRequest(unittest.TestCase):
    def test_missing_inputs_are_explicit(self):
        req = WorkRequest(
            work_id="W-1",
            title="Prepare engineering note",
            objective="Create a review package",
            required_fields=("source_file", "deadline", "reviewer"),
            inputs={"source_file": "input.pdf", "deadline": "", "reviewer": None},
        )
        self.assertEqual(req.missing_inputs(), ("deadline", "reviewer"))


class TestEventCursor(unittest.TestCase):
    def setUp(self):
        self.store = EventStore()

    def add(self, seq, kind, payload=None):
        self.store.append(
            Event(
                event_id=f"E-{seq}",
                work_id="W-42",
                sequence=seq,
                kind=kind,
                payload=payload or {},
                occurred_at=f"2026-09-08T00:00:0{min(seq,9)}+00:00",
            )
        )

    def test_rebuild_after_interruption_is_deterministic(self):
        self.add(1, EventKind.REQUEST_RECEIVED)
        self.add(2, EventKind.PLAN_CREATED, {"steps": ["validate", "analyze", "package"]})
        self.add(3, EventKind.WORK_STARTED)
        rebuilt_a = self.store.rebuild("W-42")

        serialized = list(self.store.events_for("W-42"))
        new_store = EventStore()
        for e in serialized:
            new_store.append(e)
        rebuilt_b = new_store.rebuild("W-42")

        self.assertEqual(rebuilt_a, rebuilt_b)
        self.assertEqual(rebuilt_b.state, WorkState.IN_PROGRESS)
        self.assertEqual(
            rebuilt_b.resume_pointer,
            {
                "work_id": "W-42",
                "last_applied_sequence": 3,
                "next_expected_sequence": 4,
                "state": "IN_PROGRESS",
            },
        )

    def test_duplicate_event_is_rejected(self):
        self.add(1, EventKind.REQUEST_RECEIVED)
        with self.assertRaises(DuplicateEventError):
            self.store.append(
                Event(
                    event_id="E-1",
                    work_id="W-42",
                    sequence=2,
                    kind=EventKind.PLAN_CREATED,
                    payload={"steps": ["x"]},
                )
            )

    def test_human_gate_prevents_early_completion(self):
        self.add(1, EventKind.REQUEST_RECEIVED)
        self.add(2, EventKind.PLAN_CREATED, {"steps": ["prepare", "review", "release"]})
        self.add(3, EventKind.WORK_STARTED)
        self.add(4, EventKind.HUMAN_REVIEW_REQUESTED, {"reason": "Approve release"})
        self.add(5, EventKind.WORK_COMPLETED, {"summary": "should not complete"})
        with self.assertRaises(InvalidTransition):
            self.store.rebuild("W-42")

    def test_human_approval_allows_resume_and_completion(self):
        self.add(1, EventKind.REQUEST_RECEIVED)
        self.add(2, EventKind.PLAN_CREATED, {"steps": ["prepare", "review", "release"]})
        self.add(3, EventKind.WORK_STARTED)
        evidence = EvidenceRef.from_bytes(
            "artifact-1", b"verified result", "text/plain", "test output"
        )
        self.add(
            4,
            EventKind.ARTIFACT_RECORDED,
            {
                "artifact_id": evidence.artifact_id,
                "sha256": evidence.sha256,
                "media_type": evidence.media_type,
                "description": evidence.description,
            },
        )
        self.add(5, EventKind.HUMAN_REVIEW_REQUESTED, {"reason": "Approve release"})
        self.add(6, EventKind.HUMAN_APPROVED)
        self.add(7, EventKind.WORK_COMPLETED, {"summary": "release package ready"})

        rebuilt = self.store.rebuild("W-42")
        self.assertEqual(rebuilt.state, WorkState.COMPLETED)
        self.assertEqual(len(rebuilt.evidence), 1)
        self.assertEqual(rebuilt.evidence[0].sha256, evidence.sha256)
        self.assertEqual(rebuilt.completion_summary, "release package ready")


if __name__ == "__main__":
    unittest.main()
