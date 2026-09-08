"""A bounded receiving-record reconciliation workflow, without model arithmetic."""
from __future__ import annotations

from dataclasses import asdict
import csv
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path

from .core import EventKind as K, WorkState as S
from .durable import WorkRepository, canonical, digest, safe_id


def read_csv(root: Path, relative: str, columns: set[str]):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Input must remain inside the authorized input directory")
    if path.stat().st_size > 2_000_000:
        raise ValueError("Input exceeds 2 MB limit")
    payload = path.read_bytes()
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    if set(reader.fieldnames or []) != columns or len(reader.fieldnames or []) != len(columns):
        raise ValueError("CSV headers do not match the required schema")
    rows = list(reader)
    if not rows or len(rows) > 10_000:
        raise ValueError("Expected 1 to 10000 rows")
    for row in rows:
        if any(not isinstance(v, str) or not v.strip() for v in row.values()):
            raise ValueError("CSV contains empty or malformed values")
        for key in ("line_id", "receipt_id"):
            if key in row:
                safe_id(row[key])
        try:
            quantity = Decimal(row["quantity"])
        except InvalidOperation as exc:
            raise ValueError("Invalid quantity") from exc
        if not quantity.is_finite() or quantity < 0 or quantity > 1_000_000_000:
            raise ValueError("Quantity must be finite, non-negative, and bounded")
        if quantity.as_tuple().exponent < -6 or len(row["quantity"]) > 24:
            raise ValueError("Quantity supports at most six decimal places")
    return rows, payload


class ProfessionalWorkflow:
    def __init__(self, repository: WorkRepository, work_id: str, input_root: str | Path):
        self.repo, self.work_id = repository, work_id
        self.input_root = Path(input_root).resolve()
        with self.repo.transaction() as db:
            req = self.repo.request(db, work_id)
            if not {"orders_csv", "deliveries_csv", "reviewer"}.issubset(req.required_fields):
                raise ValueError("The workflow requires orders_csv, deliveries_csv and reviewer")

    def provide_inputs(self, inputs: dict):
        with self.repo.transaction() as db:
            state = self.repo.rebuilt(db, self.work_id)
            if state.state not in {S.RECEIVED, S.NEEDS_INPUT}:
                raise ValueError("Inputs are frozen after work starts")
            req = self.repo.request(db, self.work_id)
            if set(inputs) - set(req.missing_inputs()):
                raise ValueError("Only genuinely missing fields can be supplied")
            body = asdict(req)
            body["inputs"] = {**body["inputs"], **inputs}
            db.execute("UPDATE requests SET body=? WHERE work_id=?", (canonical(body), self.work_id))
            self.repo.emit(db, self.work_id, K.MISSING_INPUTS_DETECTED,
                           {"fields": list(self.repo.request(db, self.work_id).missing_inputs()),
                            "request_sha256": digest(canonical(body))})

    def inspect_request(self):
        with self.repo.transaction() as db:
            state = self.repo.rebuilt(db, self.work_id)
            req = self.repo.request(db, self.work_id)
            missing = req.missing_inputs()
            if missing:
                if state.state != S.NEEDS_INPUT or state.missing_inputs != missing:
                    self.repo.emit(db, self.work_id, K.MISSING_INPUTS_DETECTED, {"fields": list(missing)})
                return {"state": "NEEDS_INPUT", "missing": list(missing)}
            return {"state": state.state.value, "missing": [],
                    "objective": req.objective, "next": "reconcile_delivery"}

    def reconcile_delivery(self):
        with self.repo.transaction() as db:
            prior = self.repo.receipt(db, self.work_id, "reconcile")
            if prior:
                self.repo.read_artifact(db, self.work_id, "reconciliation.json")
                return {**prior, "reused": True}
            state = self.repo.rebuilt(db, self.work_id)
            if state.state not in {S.RECEIVED, S.NEEDS_INPUT}:
                raise ValueError("Reconciliation is not allowed in this state")
            req = self.repo.request(db, self.work_id)
            if req.missing_inputs():
                raise ValueError("Required inputs are still missing")
            orders, order_bytes = read_csv(self.input_root, req.inputs["orders_csv"], {"line_id", "item", "quantity"})
            receipts, delivery_bytes = read_csv(self.input_root, req.inputs["deliveries_csv"], {"receipt_id", "line_id", "quantity"})
            if len({r["line_id"] for r in orders}) != len(orders):
                raise ValueError("Duplicate order line IDs")
            if len({r["receipt_id"] for r in receipts}) != len(receipts):
                raise ValueError("Duplicate receipt IDs; refusing double-counted deliveries")
            totals = {}
            for row in receipts:
                totals[row["line_id"]] = totals.get(row["line_id"], Decimal(0)) + Decimal(row["quantity"])
            rows = []
            for order in orders:
                received = totals.pop(order["line_id"], Decimal(0))
                difference = received - Decimal(order["quantity"])
                rows.append({"line_id": order["line_id"], "item": order["item"],
                             "ordered": str(Decimal(order["quantity"])), "received": str(received),
                             "difference": str(difference),
                             "status": "MATCH" if difference == 0 else ("SHORT" if difference < 0 else "OVER")})
            result = {"work_id": self.work_id, "lines": rows,
                      "unmatched_receipts": {k: str(v) for k, v in sorted(totals.items())},
                      "discrepancy_count": sum(r["status"] != "MATCH" for r in rows) + len(totals),
                      "source_hashes": {"orders.csv": digest(order_bytes), "deliveries.csv": digest(delivery_bytes)},
                      "method": "Exact Decimal quantity comparison; human review required for release"}
            self.repo.emit(db, self.work_id, K.PLAN_CREATED, {"steps": ["validate source records", "reconcile quantities", "prepare evidence", "human release"]})
            self.repo.emit(db, self.work_id, K.WORK_STARTED)
            self.repo.artifact(db, self.work_id, "orders.csv", order_bytes, "text/csv")
            self.repo.artifact(db, self.work_id, "deliveries.csv", delivery_bytes, "text/csv")
            evidence = self.repo.artifact(db, self.work_id, "reconciliation.json", canonical(result), "application/json")
            receipt = {"state": "IN_PROGRESS", "discrepancy_count": result["discrepancy_count"],
                       "evidence": evidence, "reused": False}
            self.repo.save_receipt(db, self.work_id, "reconcile", receipt)
            return receipt

    def prepare_review_package(self):
        with self.repo.transaction() as db:
            prior = self.repo.receipt(db, self.work_id, "review")
            if prior:
                return {**prior, "reused": True}
            if not self.repo.receipt(db, self.work_id, "reconcile"):
                raise ValueError("Reconcile source records before requesting review")
            result = json.loads(self.repo.read_artifact(db, self.work_id, "reconciliation.json"))
            text = ["# Receiving reconciliation — draft for human review", "",
                    "The comparison below uses the attached source records and exact decimal arithmetic.", "",
                    "| Line | Ordered | Received | Difference | State |", "|---|---:|---:|---:|---|"]
            for row in result["lines"]:
                # Keep untrusted source strings out of the report markup.
                text.append(f"| {row['line_id'].replace('|', ' ')} | {row['ordered']} | {row['received']} | {row['difference']} | {row['status']} |")
            text.extend(["", f"Unmatched receipt lines: {len(result['unmatched_receipts'])}.",
                         f"Discrepancies requiring review: {result['discrepancy_count']}.",
                         "", "No external action or release has been authorized by the agent."])
            self.repo.artifact(db, self.work_id, "review.md", "\n".join(text).encode(), "text/markdown")
            self.repo.emit(db, self.work_id, K.HUMAN_REVIEW_REQUESTED, {"reason": "Approve or reject issuing this receiving reconciliation package"})
            receipt = {"state": "HUMAN_REVIEW", "next_action": "HUMAN_DECISION", "reused": False}
            self.repo.save_receipt(db, self.work_id, "review", receipt)
            return receipt

    def decide(self, *, approve: bool, reviewer: str):
        # Operator-only entrypoint. Deliberately absent from the model's tools.
        with self.repo.transaction() as db:
            request = self.repo.request(db, self.work_id)
            if not reviewer or reviewer != request.inputs["reviewer"]:
                raise PermissionError("The configured human reviewer is required")
            previous = self.repo.receipt(db, self.work_id, "decision")
            if previous:
                if previous["approved"] != approve:
                    raise ValueError("A different decision is already durable")
                return previous
            if self.repo.rebuilt(db, self.work_id).state != S.HUMAN_REVIEW:
                raise ValueError("No pending human review")
            # Verify all content before permitting release.
            state = self.repo.rebuilt(db, self.work_id)
            for ref in state.evidence:
                if digest(self.repo.read_artifact(db, self.work_id, ref.artifact_id)) != ref.sha256:
                    raise ValueError("Evidence changed before review")
            if approve:
                self.repo.emit(db, self.work_id, K.HUMAN_APPROVED, {"decision_source": "operator_cli"})
                manifest = {"work_id": self.work_id, "approved": True,
                            "artifacts": [asdict(ref) for ref in state.evidence]}
                self.repo.artifact(db, self.work_id, "release-manifest.json", canonical(manifest), "application/json")
                self.repo.emit(db, self.work_id, K.WORK_COMPLETED, {"summary": "Human-approved receiving reconciliation package"})
            else:
                self.repo.emit(db, self.work_id, K.HUMAN_REJECTED, {"reason": "Operator rejected release"})
            receipt = {"approved": approve, "state": "COMPLETED" if approve else "FAILED"}
            self.repo.save_receipt(db, self.work_id, "decision", receipt)
            return receipt
