"""Cloud Run compatible HTTP surface."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .adk_fleet import (
    ELIGIBLE_MODEL,
    run_live_gemini_payload,
    run_live_pae006_payload,
)
from .agents import AgentFleet, default_registry_path
from .state import SQLiteStateStore

ROOT = Path(__file__).resolve().parents[2]
STORE = SQLiteStateStore(os.getenv("WEXSPACE_DB", "/tmp/wexspace/workflows.db"))
FLEET = AgentFleet(
    STORE,
    os.getenv("WEXSPACE_AGENT_REGISTRY", str(default_registry_path())),
)
app = FastAPI(title="WEXSPACE AI — IEW Agentic Engineering Fleet", version=__version__)


class WorkflowRequest(BaseModel):
    goal: str = "Analyze synthetic cooling-water network"
    engineering_input: dict[str, Any]
    asynchronous: bool = False


class ReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": __version__,
        "state_backend": "sqlite-demo",
        "google_cloud_deployment": os.getenv("K_SERVICE") is not None,
    }


@app.get("/agents")
def agents() -> dict[str, Any]:
    return FLEET.registry


@app.post("/workflows")
def create_workflow(request: WorkflowRequest) -> dict[str, Any]:
    return FLEET.start(
        request.goal,
        request.engineering_input,
        run_immediately=not request.asynchronous,
    )


@app.post("/worker/once")
def worker_once() -> dict[str, Any]:
    result = FLEET.worker_once()
    return {"processed": result is not None, "workflow": result}


@app.post("/adk/live")
async def live_adk_workflow(request: WorkflowRequest) -> dict[str, Any]:
    """Run the Gemini-backed ADK fleet through the configured Google route."""
    result = await run_live_gemini_payload(request.engineering_input)
    if not result["passed"]:
        raise HTTPException(status_code=503, detail=result)
    return result


@app.post("/adk/pae006/fresh")
async def live_pae006_adk_workflow(request: WorkflowRequest) -> dict[str, Any]:
    """Run the bounded fresh PAE-006 study through Google ADK and Gemini."""
    result = await run_live_pae006_payload(request.engineering_input)
    if not result["passed"]:
        raise HTTPException(status_code=503, detail=result)
    return result


@app.get("/workflows/{workflow_id}")
def workflow_status(workflow_id: str) -> dict[str, Any]:
    try:
        return FLEET.status(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc


@app.post("/workflows/{workflow_id}/review")
def review(workflow_id: str, request: ReviewRequest) -> dict[str, Any]:
    try:
        return FLEET.approve(workflow_id, request.reviewer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
