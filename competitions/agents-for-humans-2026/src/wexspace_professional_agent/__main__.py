"""Trusted local operator CLI. No public network service or credential collection."""
import argparse
import asyncio
import json
from pathlib import Path

from .core import WorkRequest
from .durable import WorkRepository
from .strands_adapter import ProviderAuthRequired, run_workflow
from .workflow import ProfessionalWorkflow


def main():
    parser = argparse.ArgumentParser(description="WEXSPACE Professional Evidence Agent")
    parser.add_argument("--state-dir", default=".wexspace-state")
    parser.add_argument("--input-dir", default="examples")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("request_file")
    for name in ("run", "status", "provide-inputs", "review", "export"):
        sub = commands.add_parser(name)
        sub.add_argument("work_id")
        if name == "provide-inputs":
            sub.add_argument("inputs_file")
        elif name == "review":
            sub.add_argument("--reviewer", required=True)
            group = sub.add_mutually_exclusive_group(required=True)
            group.add_argument("--approve", action="store_true")
            group.add_argument("--reject", action="store_true")
        elif name == "export":
            sub.add_argument("directory")
    args = parser.parse_args()
    root = Path(args.state_dir)
    repo = WorkRepository(root / "work.sqlite3")
    try:
        if args.command == "create":
            req = json.loads(Path(args.request_file).read_text())
            # Workflow-owned contract: the caller supplies facts, never bypasses required fields.
            request = WorkRequest(work_id=req["work_id"], title=req["title"], objective=req["objective"],
                                  required_fields=("orders_csv", "deliveries_csv", "reviewer"),
                                  inputs=req["inputs"], required_deliverables=("reconciliation.json", "review.md"))
            repo.register(request)
            result = repo.status(request.work_id)
        else:
            workflow = ProfessionalWorkflow(repo, args.work_id, args.input_dir)
            if args.command == "run":
                result = asyncio.run(run_workflow(workflow, root / "agent"))
            elif args.command == "provide-inputs":
                workflow.provide_inputs(json.loads(Path(args.inputs_file).read_text()))
                result = repo.status(args.work_id)
            elif args.command == "review":
                result = workflow.decide(approve=args.approve, reviewer=args.reviewer)
            elif args.command == "export":
                result = {"exported": str(repo.export(args.work_id, args.directory))}
            else:
                result = repo.status(args.work_id)
        print(json.dumps(result, indent=2))
    except ProviderAuthRequired:
        print(json.dumps({"state": "PROVIDER_AUTH_REQUIRED", "provider_invoked": False,
                          "human_prompt_created": False, "next": "Configure Google access on an authorized execution host"}))
        return 3
    except (ValueError, KeyError, PermissionError) as exc:
        print(json.dumps({"state": "ACTION_REJECTED", "error_type": type(exc).__name__}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
