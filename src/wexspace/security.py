"""Application-level governance and input-scope controls."""

from __future__ import annotations

from typing import Any

FORBIDDEN_PATTERNS = (
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "reveal secret",
    "show api key",
    "exfiltrate",
    "run shell",
    "execute command",
    "disable policy",
)


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def policy_check(goal: str, payload: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    for text in [goal, *_strings(payload)]:
        lowered = text.lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in lowered:
                findings.append(f"blocked pattern: {pattern}")
    allowed_goal = goal.strip().lower() in {
        "analyze synthetic cooling-water network",
        "analyse synthetic cooling-water network",
    }
    if not allowed_goal:
        findings.append("goal is outside the demo authority scope")
    return {
        "policy_id": "WEX-POLICY-001",
        "allowed": not findings,
        "findings": sorted(set(findings)),
        "data_scope": "synthetic neutral cooling-water network only",
        "write_scope": "controlled workflow state and evidence only",
        "secret_values_logged": False,
    }

