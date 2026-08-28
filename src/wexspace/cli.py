"""CLI for local execution, asynchronous worker, and restart/resume proof."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .agents import AgentFleet, default_registry_path
from .state import SQLiteStateStore


def _fleet(args: argparse.Namespace) -> AgentFleet:
    store = SQLiteStateStore(args.db)
    return AgentFleet(store, args.registry)


def _emit(value) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(prog="wexspace-fleet")
    p.add_argument("--db", default=os.getenv("WEXSPACE_DB", str(root / "data" / "workflows.db")))
    p.add_argument(
        "--registry",
        default=os.getenv("WEXSPACE_AGENT_REGISTRY", str(default_registry_path())),
    )
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument(
        "--goal", default="Analyze synthetic cooling-water network"
    )
    run.add_argument("--pause-after", choices=["engineering"])
    queue = sub.add_parser("queue")
    queue.add_argument("--input", required=True)
    queue.add_argument("--goal", default="Analyze synthetic cooling-water network")
    resume = sub.add_parser("resume")
    resume.add_argument("workflow_id")
    approve = sub.add_parser("approve")
    approve.add_argument("workflow_id")
    approve.add_argument("--reviewer", required=True)
    status = sub.add_parser("status")
    status.add_argument("workflow_id")
    sub.add_parser("worker-once")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    fleet = _fleet(args)
    if args.command in {"run", "queue"}:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = fleet.start(
            args.goal,
            payload,
            pause_after=getattr(args, "pause_after", None),
            run_immediately=args.command == "run",
        )
    elif args.command == "resume":
        result = fleet.resume(args.workflow_id)
    elif args.command == "approve":
        result = fleet.approve(args.workflow_id, args.reviewer)
    elif args.command == "status":
        result = fleet.status(args.workflow_id)
    else:
        result = fleet.worker_once()
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
