"""Application-level governance, context, and input-scope controls."""

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

COMPETITION_CONTEXT_ALLOWLIST_ID = "WEXSPACE-COMPETITION-ALLOWLIST-R07"
COMPETITION_CONTEXT_ALLOWLIST = frozenset(
    {
        "WEXSPACE_AI_PRODUCT_PLATFORM",
        "IEW_AI_COMPETITION_CONTINUITY",
        "GOOGLE_ALL_THINGS_AGENTIC_2026",
        "UTL_NET_001_NEUTRAL_DEMO",
        "COMPETITION_REPOSITORY",
        "GOOGLE_CLOUD_COMPETITION",
        "GEMINI_GOOGLE_ADK",
        "GOOGLE_DRIVE_COMPETITION_EVIDENCE",
        "DEVPOST_COMPETITION",
        "OFFICIAL_COMPETITION_RESOURCES",
        "APPROVED_NEUTRAL_DEPENDENCY",
    }
)

DEFAULT_DEMO_CONTEXT = {
    "source_id": "UTL-NET-001-HACKATHON-SYNTHETIC",
    "family": "UTL_NET_001_NEUTRAL_DEMO",
    "authority": True,
    "relevance": True,
    "scope_compatibility": True,
}


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


def _context_gate(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply lineage-based competition context isolation.

    Context is accepted only when its family is explicitly allowlisted and the
    caller supplies affirmative authority, relevance, and scope compatibility.
    The controlled synthetic demo receives one bounded derived source record
    when no external context sources are supplied.
    """
    raw_sources = payload.get("context_sources")
    validation_errors: list[str] = []
    if raw_sources is None:
        raw_sources = [dict(DEFAULT_DEMO_CONTEXT)]
    elif not isinstance(raw_sources, list) or not raw_sources:
        validation_errors.append("context_sources must be a non-empty array when provided")
        raw_sources = []

    sources: list[dict[str, Any]] = []
    for index, source in enumerate(raw_sources):
        if not isinstance(source, dict):
            validation_errors.append(f"context_sources[{index}] must be an object")
            continue
        family = str(source.get("family", "")).strip()
        authority = source.get("authority") is True
        relevance = source.get("relevance") is True
        scope_compatibility = source.get("scope_compatibility") is True
        authorized = (
            family in COMPETITION_CONTEXT_ALLOWLIST
            and authority
            and relevance
            and scope_compatibility
        )
        record = {
            "source_id": str(source.get("source_id", f"context-source-{index}")),
            "family": family or "UNDECLARED",
            "authority": authority,
            "relevance": relevance,
            "scope_compatibility": scope_compatibility,
            "classification": "AUTHORIZED_DEPENDENCY" if authorized else "DO_NOT_USE",
        }
        sources.append(record)
        if not authorized:
            validation_errors.append(
                f"context_sources[{index}] failed authority + relevance + scope compatibility"
            )

    return {
        "allowlist_id": COMPETITION_CONTEXT_ALLOWLIST_ID,
        "out_of_scope_default": "DO_NOT_USE",
        "sources": sources,
        "validation_errors": validation_errors,
        "allowed": bool(sources) and not validation_errors,
    }


def _scope_relevance_actionability(goal: str) -> dict[str, Any]:
    normalized = goal.strip().lower()
    relevant = normalized in {
        "analyze synthetic cooling-water network",
        "analyse synthetic cooling-water network",
    }
    return {
        "information_owner": "USER",
        "action_owner": "WEXSPACE_GOVERNING_AGENT",
        "authority_owner": "USER",
        "execution_owner": "WEXSPACE_AGENT_FLEET",
        "verification_owner": "WEXSPACE_VERIFICATION_EVIDENCE_SPECIALIST",
        "scope_state": "WORK_MANAGED" if relevant else "OUT_OF_SCOPE",
        "relevance_state": "CURRENT_CRITICAL" if relevant else "OUT_OF_SCOPE",
        "actionability_state": "ACTIONABLE_NOW" if relevant else "DO_NOT_ACT",
        "allowed": relevant,
    }


def policy_check(goal: str, payload: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    for text in [goal, *_strings(payload)]:
        lowered = text.lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in lowered:
                findings.append(f"blocked pattern: {pattern}")
    context_gate = _context_gate(payload)
    scope_contract = _scope_relevance_actionability(goal)
    if not scope_contract["allowed"]:
        findings.append("goal is outside the demo authority scope")
    findings.extend(context_gate["validation_errors"])
    if payload.get("project_id") not in {
        "UTL-NET-001-HACKATHON-SYNTHETIC",
        "UTL-NET-001-MISSING-INPUT-DEMO",
    }:
        findings.append("project identity is outside the neutral competition demo scope")
    return {
        "policy_id": "WEX-POLICY-001",
        "allowed": not findings,
        "findings": sorted(set(findings)),
        "context_gate": context_gate,
        "scope_relevance_actionability": scope_contract,
        "data_scope": "synthetic neutral cooling-water network only",
        "write_scope": "controlled workflow state and evidence only",
        "secret_values_logged": False,
    }
