"""Challenge-new SQLite persistence around the unchanged R01 event kernel."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from .core import Event, EventKind, EventStore, WorkRequest


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def atomic_write(path: Path, payload: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def safe_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise ValueError("Expected a bounded work identifier")
    return value


class IntegrityError(ValueError):
    pass


class WorkRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS requests (
                    work_id TEXT PRIMARY KEY, body BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    work_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                    body BLOB NOT NULL, sha256 TEXT NOT NULL,
                    PRIMARY KEY(work_id, sequence));
                CREATE TABLE IF NOT EXISTS artifacts (
                    work_id TEXT NOT NULL, name TEXT NOT NULL,
                    media_type TEXT NOT NULL, payload BLOB NOT NULL,
                    sha256 TEXT NOT NULL, PRIMARY KEY(work_id, name));
                CREATE TABLE IF NOT EXISTS receipts (
                    work_id TEXT NOT NULL, operation TEXT NOT NULL,
                    body BLOB NOT NULL, PRIMARY KEY(work_id, operation));
            ''')

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _load(self, db, work_id):
        store = EventStore()
        parent = ""
        for body, sha in db.execute("SELECT body,sha256 FROM events WHERE work_id=? ORDER BY sequence", (work_id,)):
            if digest(parent.encode() + body) != sha:
                raise IntegrityError("Event chain integrity mismatch")
            value = json.loads(body)
            value["kind"] = EventKind(value["kind"])
            store.append(Event(**value))
            parent = sha
        return store, parent

    def emit(self, db, work_id, kind, payload=None):
        store, parent = self._load(db, work_id)
        event = Event(f"{work_id}-{len(store.events_for(work_id))+1}", work_id,
                      len(store.events_for(work_id))+1, kind, payload or {})
        store.append(event)
        store.rebuild(work_id)  # validate before durable commit
        body = event.canonical_json().encode()
        db.execute("INSERT INTO events VALUES (?,?,?,?)", (work_id, event.sequence, body, digest(parent.encode()+body)))
        return event

    def request(self, db, work_id):
        row = db.execute("SELECT body FROM requests WHERE work_id=?", (work_id,)).fetchone()
        if row is None:
            raise KeyError(work_id)
        value = json.loads(row[0])
        value["required_fields"] = tuple(value["required_fields"])
        value["required_deliverables"] = tuple(value["required_deliverables"])
        return WorkRequest(**value)

    def register(self, request: WorkRequest):
        safe_id(request.work_id)
        body = canonical(asdict(request))
        with self.transaction() as db:
            row = db.execute("SELECT body FROM requests WHERE work_id=?", (request.work_id,)).fetchone()
            if row:
                if row[0] != body:
                    raise ValueError("Work ID already belongs to a different request")
                return
            db.execute("INSERT INTO requests VALUES (?,?)", (request.work_id, body))
            self.emit(db, request.work_id, EventKind.REQUEST_RECEIVED, {"request_sha256": digest(body)})

    def rebuilt(self, db, work_id):
        return self._load(db, work_id)[0].rebuild(work_id)

    def receipt(self, db, work_id, operation):
        row = db.execute("SELECT body FROM receipts WHERE work_id=? AND operation=?", (work_id, operation)).fetchone()
        return json.loads(row[0]) if row else None

    def save_receipt(self, db, work_id, operation, value):
        db.execute("INSERT INTO receipts VALUES (?,?,?)", (work_id, operation, canonical(value)))

    def artifact(self, db, work_id, name, payload: bytes, media_type: str):
        # Names are application constants; the model never chooses filesystem paths.
        if Path(name).name != name:
            raise ValueError("Artifact name must be a basename")
        sha = digest(payload)
        db.execute("INSERT INTO artifacts VALUES (?,?,?,?,?)", (work_id, name, media_type, payload, sha))
        evidence = {"artifact_id": name, "sha256": sha, "media_type": media_type}
        self.emit(db, work_id, EventKind.ARTIFACT_RECORDED, evidence)
        return evidence

    def read_artifact(self, db, work_id, name):
        row = db.execute("SELECT payload,sha256 FROM artifacts WHERE work_id=? AND name=?", (work_id, name)).fetchone()
        if not row:
            raise KeyError(name)
        if digest(row[0]) != row[1]:
            raise IntegrityError("Artifact integrity mismatch")
        return row[0]

    def status(self, work_id):
        with self.transaction() as db:
            state = self.rebuilt(db, work_id)
            for ref in state.evidence:
                if digest(self.read_artifact(db, work_id, ref.artifact_id)) != ref.sha256:
                    raise IntegrityError("Evidence reference mismatch")
            return {**state.resume_pointer, "missing_inputs": list(state.missing_inputs),
                    "evidence": [asdict(x) for x in state.evidence],
                    "next_action": "HUMAN_DECISION" if state.state.value == "HUMAN_REVIEW" else state.state.value}

    def export(self, work_id, directory):
        target = Path(directory) / safe_id(work_id)
        target.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            state = self.rebuilt(db, work_id)
            for ref in state.evidence:
                data = self.read_artifact(db, work_id, ref.artifact_id)
                if digest(data) != ref.sha256:
                    raise IntegrityError("Evidence reference mismatch")
                path = target / ref.artifact_id
                if path.exists() and path.read_bytes() != data:
                    raise IntegrityError("Refusing to overwrite changed exported evidence")
                if not path.exists():
                    atomic_write(path, data)
        return target
