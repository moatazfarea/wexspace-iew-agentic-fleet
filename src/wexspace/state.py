"""Transactional workflow state and structured operational trace."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteStateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    result_json TEXT,
                    verification_json TEXT,
                    evidence_json TEXT,
                    review_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id)
                );
                """
            )

    def create_workflow(self, workflow_id: str, goal: str, payload: dict[str, Any]) -> None:
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO workflows
                (workflow_id, goal, input_json, status, current_step, created_at, updated_at)
                VALUES (?, ?, ?, 'QUEUED', 'GOVERNANCE', ?, ?)""",
                (workflow_id, goal, json.dumps(payload, sort_keys=True), now, now),
            )

    def update(self, workflow_id: str, **fields: Any) -> None:
        allowed = {
            "status",
            "current_step",
            "result_json",
            "verification_json",
            "evidence_json",
            "review_json",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"unsupported workflow fields: {sorted(unknown)}")
        encoded: dict[str, Any] = {}
        for key, value in fields.items():
            encoded[key] = json.dumps(value, sort_keys=True) if key.endswith("_json") else value
        encoded["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in encoded)
        with self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE workflows SET {assignments} WHERE workflow_id = ?",
                (*encoded.values(), workflow_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(workflow_id)

    def get(self, workflow_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,)
            ).fetchone()
        if row is None:
            raise KeyError(workflow_id)
        result = dict(row)
        for key in (
            "input_json",
            "result_json",
            "verification_json",
            "evidence_json",
            "review_json",
        ):
            result[key[:-5] if key.endswith("_json") else key] = (
                json.loads(result[key]) if result[key] else None
            )
            del result[key]
        return result

    def list_by_status(self, statuses: tuple[str, ...]) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in statuses)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT workflow_id FROM workflows WHERE status IN ({placeholders}) ORDER BY created_at",
                statuses,
            ).fetchall()
        return [self.get(row["workflow_id"]) for row in rows]

    def add_event(
        self,
        workflow_id: str,
        agent_id: str,
        event_type: str,
        outcome: str,
        details: dict[str, Any],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO events
                (workflow_id, timestamp, agent_id, event_type, outcome, details_json)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    workflow_id,
                    utc_now(),
                    agent_id,
                    event_type,
                    outcome,
                    json.dumps(details, sort_keys=True),
                ),
            )

    def events(self, workflow_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE workflow_id = ? ORDER BY event_id", (workflow_id,)
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["details"] = json.loads(item.pop("details_json"))
            result.append(item)
        return result

