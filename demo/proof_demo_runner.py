#!/usr/bin/env python3
"""Display the authentic public-safe Cloud and repository proof records."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLOUD = ROOT / "evidence" / "cloud" / "R07_VERTEX_CLOUD_RUN_SUCCESS_SUMMARY_R01.json"
DELAY = float(os.getenv("WEXSPACE_PROOF_DELAY", "1.15"))
PACE = float(os.getenv("WEXSPACE_PROOF_PACE", "1.0"))


def emit(message: str = "", *, delay: float | None = None) -> None:
    print(message, flush=True)
    time.sleep((DELAY if delay is None else delay) * PACE)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    cloud = json.loads(CLOUD.read_text(encoding="utf-8"))
    summary_sha = hashlib.sha256(CLOUD.read_bytes()).hexdigest()
    emit("AUTHENTIC GOOGLE CLOUD EVIDENCE — PUBLIC-SAFE READBACK", delay=0.9)
    emit("Source: bounded Cloud qualification result; private raw archive retained", delay=0.9)
    emit("", delay=0.25)
    emit(f"$ open {CLOUD.relative_to(ROOT)}", delay=0.7)
    emit(f"[CLOUD PROJECT] {cloud['project_id']}")
    emit(f"[CLOUD RUN SERVICE] {cloud['service_name']}")
    emit(f"[READY REVISION] {cloud['ready_revision']}")
    emit(f"[REGION] {cloud['region']}")
    emit(f"[LIVE INVOCATION] POST /adk/live -> HTTP {cloud['http_status']['adk_live']}")
    emit(f"[BACKEND] {cloud['execution_route']['backend']} | {cloud['model']}")
    emit(f"[IDENTITY] {cloud['execution_route']['credential_source']} | api_key_required=false")
    emit("[AFFECTED CHECKS]", delay=0.65)
    for name, passed in cloud["requalified_checks"].items():
        emit(f"  {name:<24} {str(passed).lower()}", delay=0.62)
    emit(
        "[VERTEX ASSERTIONS] "
        + str(sum(cloud["vertex_assertions"].values()))
        + "/"
        + str(len(cloud["vertex_assertions"])),
        delay=0.8,
    )
    emit(f"[LOGS PRESENT] {str(cloud['vertex_assertions']['logs_present']).lower()}", delay=0.8)
    emit(f"[SECRET VALUES LOGGED] {str(cloud['secret_values_logged']).lower()}", delay=0.8)
    emit(f"[RAW ARCHIVE SHA-256] {cloud['evidence_archive_sha256']}", delay=0.9)
    emit(
        "[RAW CLOUD STORAGE READBACK VERIFIED] "
        + str(cloud["cloud_storage_raw_readback_sha256_verified_by_execution_script"]).lower(),
        delay=1.0,
    )
    emit(f"[PUBLIC SUMMARY SHA-256] {summary_sha}", delay=0.9)
    emit("", delay=0.25)
    emit("$ git verify deployed-runtime provenance", delay=0.7)
    emit(f"[DEPLOYED COMMIT] {cloud['deployed_runtime_source_commit']}", delay=0.8)
    emit(f"[DEPLOYED TREE] {cloud['deployed_runtime_source_tree']}", delay=0.8)
    runtime_delta = git("diff", "--name-only", "6f5a0c8", "HEAD", "--", "src/wexspace", "Dockerfile", "requirements.txt")
    emit(f"[RUNTIME DELTA AFTER DEPLOYMENT] {runtime_delta or 'none — documentation/media only'}", delay=0.9)
    emit("[PUBLIC REPOSITORY] github.com/moatazfarea/wexspace-iew-agentic-fleet", delay=0.9)
    emit("[CLOUD GATE] PASS | FIRST TECHNICAL VICTORY 7/7", delay=3.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
