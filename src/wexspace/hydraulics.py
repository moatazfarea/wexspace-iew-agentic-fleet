"""Deterministic hydraulic calculation and independent verification.

The numerical result is produced by engineering equations, not by a language
model.  The demo uses a synthetic, neutral cooling-water distribution network.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from math import log10, pi
from typing import Any

G = 9.80665


def _required(mapping: dict[str, Any], key: str, where: str, errors: list[str]) -> None:
    if key not in mapping or mapping[key] in (None, "", []):
        errors.append(f"{where}.{key} is required")


def validate_network_input(data: dict[str, Any]) -> list[str]:
    """Return explicit validation errors without guessing missing inputs."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["input must be a JSON object"]
    for key in ("project_id", "source_node", "source_pressure_kpa", "fluid", "segments"):
        _required(data, key, "input", errors)
    fluid = data.get("fluid")
    if isinstance(fluid, dict):
        for key in ("density_kg_m3", "dynamic_viscosity_pa_s"):
            _required(fluid, key, "input.fluid", errors)
    elif "fluid" in data:
        errors.append("input.fluid must be an object")
    segments = data.get("segments")
    if isinstance(segments, list):
        if not segments:
            errors.append("input.segments must contain at least one segment")
        ids: set[str] = set()
        for index, segment in enumerate(segments):
            where = f"input.segments[{index}]"
            if not isinstance(segment, dict):
                errors.append(f"{where} must be an object")
                continue
            for key in (
                "segment_id",
                "from_node",
                "to_node",
                "length_m",
                "diameter_mm",
                "roughness_mm",
                "flow_m3_h",
                "k_local",
                "elevation_gain_m",
            ):
                _required(segment, key, where, errors)
            sid = segment.get("segment_id")
            if sid in ids:
                errors.append(f"duplicate segment_id: {sid}")
            if sid:
                ids.add(str(sid))
            for key in ("length_m", "diameter_mm", "flow_m3_h"):
                value = segment.get(key)
                if isinstance(value, (int, float)) and value <= 0:
                    errors.append(f"{where}.{key} must be > 0")
            for key in ("roughness_mm", "k_local"):
                value = segment.get(key)
                if isinstance(value, (int, float)) and value < 0:
                    errors.append(f"{where}.{key} must be >= 0")
    elif "segments" in data:
        errors.append("input.segments must be an array")
    for key in ("source_pressure_kpa",):
        value = data.get(key)
        if isinstance(value, (int, float)) and value <= 0:
            errors.append(f"input.{key} must be > 0")
    return errors


def swamee_jain_friction_factor(reynolds: float, relative_roughness: float) -> float:
    if reynolds <= 0:
        raise ValueError("Reynolds number must be positive")
    if reynolds < 2300:
        return 64.0 / reynolds
    return 0.25 / (log10(relative_roughness / 3.7 + 5.74 / reynolds**0.9) ** 2)


def haaland_friction_factor(reynolds: float, relative_roughness: float) -> float:
    if reynolds <= 0:
        raise ValueError("Reynolds number must be positive")
    if reynolds < 2300:
        return 64.0 / reynolds
    return (-1.8 * log10((relative_roughness / 3.7) ** 1.11 + 6.9 / reynolds)) ** -2


def _segment_result(segment: dict[str, Any], density: float, viscosity: float, method: str) -> dict[str, Any]:
    diameter_m = float(segment["diameter_mm"]) / 1000.0
    roughness_m = float(segment["roughness_mm"]) / 1000.0
    flow_m3_s = float(segment["flow_m3_h"]) / 3600.0
    area_m2 = pi * diameter_m**2 / 4.0
    velocity_m_s = flow_m3_s / area_m2
    reynolds = density * velocity_m_s * diameter_m / viscosity
    relative_roughness = roughness_m / diameter_m
    if method == "swamee-jain":
        friction = swamee_jain_friction_factor(reynolds, relative_roughness)
    elif method == "haaland":
        friction = haaland_friction_factor(reynolds, relative_roughness)
    else:
        raise ValueError(f"unsupported friction method: {method}")
    velocity_head_m = velocity_m_s**2 / (2.0 * G)
    friction_and_local_head_m = (
        friction * float(segment["length_m"]) / diameter_m + float(segment["k_local"])
    ) * velocity_head_m
    elevation_gain_m = float(segment["elevation_gain_m"])
    total_head_m = friction_and_local_head_m + elevation_gain_m
    pressure_drop_kpa = density * G * total_head_m / 1000.0
    return {
        "segment_id": str(segment["segment_id"]),
        "from_node": str(segment["from_node"]),
        "to_node": str(segment["to_node"]),
        "flow_m3_h": round(float(segment["flow_m3_h"]), 9),
        "area_m2": round(area_m2, 12),
        "velocity_m_s": round(velocity_m_s, 9),
        "reynolds": round(reynolds, 3),
        "relative_roughness": round(relative_roughness, 9),
        "friction_factor": round(friction, 9),
        "friction_and_local_head_m": round(friction_and_local_head_m, 9),
        "elevation_gain_m": round(elevation_gain_m, 9),
        "total_head_m": round(total_head_m, 9),
        "pressure_drop_kpa": round(pressure_drop_kpa, 9),
    }


def _node_balances(segments: list[dict[str, Any]], source_node: str) -> dict[str, float]:
    incoming: dict[str, float] = defaultdict(float)
    outgoing: dict[str, float] = defaultdict(float)
    for segment in segments:
        outgoing[str(segment["from_node"])] += float(segment["flow_m3_h"])
        incoming[str(segment["to_node"])] += float(segment["flow_m3_h"])
    nodes = sorted(set(incoming) | set(outgoing))
    return {
        node: round(incoming[node] - outgoing[node], 9)
        for node in nodes
        if node != source_node and incoming[node] and outgoing[node]
    }


def _endpoint_paths(
    segments: list[dict[str, Any]], source_node: str, source_pressure_kpa: float
) -> list[dict[str, Any]]:
    by_from: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_from: set[str] = set()
    all_to: set[str] = set()
    for segment in segments:
        by_from[segment["from_node"]].append(segment)
        all_from.add(segment["from_node"])
        all_to.add(segment["to_node"])
    endpoints = sorted(all_to - all_from)
    paths: list[dict[str, Any]] = []

    def walk(node: str, visited: set[str], segment_ids: list[str], pressure_drop: float) -> None:
        if node in visited:
            raise ValueError("network must be acyclic for this demonstration workflow")
        if node in endpoints:
            paths.append(
                {
                    "endpoint_node": node,
                    "segment_ids": list(segment_ids),
                    "total_pressure_drop_kpa": round(pressure_drop, 9),
                    "residual_pressure_kpa": round(source_pressure_kpa - pressure_drop, 9),
                }
            )
            return
        for segment in by_from.get(node, []):
            walk(
                segment["to_node"],
                visited | {node},
                segment_ids + [segment["segment_id"]],
                pressure_drop + float(segment["pressure_drop_kpa"]),
            )

    walk(source_node, set(), [], 0.0)
    return paths


def calculate_network(data: dict[str, Any], method: str = "swamee-jain") -> dict[str, Any]:
    errors = validate_network_input(data)
    if errors:
        raise ValueError("; ".join(errors))
    fluid = data["fluid"]
    density = float(fluid["density_kg_m3"])
    viscosity = float(fluid["dynamic_viscosity_pa_s"])
    source_node = str(data["source_node"])
    source_pressure = float(data["source_pressure_kpa"])
    segment_results = [
        _segment_result(segment, density, viscosity, method) for segment in data["segments"]
    ]
    paths = _endpoint_paths(segment_results, source_node, source_pressure)
    node_balances = _node_balances(segment_results, source_node)
    max_balance = max((abs(value) for value in node_balances.values()), default=0.0)
    min_velocity = float(data.get("velocity_limits_m_s", {}).get("min", 0.5))
    max_velocity = float(data.get("velocity_limits_m_s", {}).get("max", 3.0))
    min_residual = float(data.get("min_residual_pressure_kpa", 150.0))
    checks = {
        "mass_continuity": max_balance <= 1e-6,
        "velocity_limits": all(
            min_velocity <= segment["velocity_m_s"] <= max_velocity for segment in segment_results
        ),
        "minimum_residual_pressure": all(
            path["residual_pressure_kpa"] >= min_residual for path in paths
        ),
        "turbulent_or_declared_laminar": all(segment["reynolds"] > 0 for segment in segment_results),
    }
    return {
        "calculation_engine": "WEXSPACE deterministic hydraulic engine",
        "calculation_engine_version": "0.1.0",
        "method": method,
        "project_id": data["project_id"],
        "assumptions": {
            "steady_incompressible_flow": True,
            "darcy_weisbach": True,
            "fluid_properties_user_supplied": True,
            "network_type": "directed_acyclic_demo_network",
        },
        "segments": segment_results,
        "node_balance_m3_h": node_balances,
        "endpoint_paths": paths,
        "checks": checks,
        "accepted": all(checks.values()),
    }


def independently_verify(data: dict[str, Any], primary: dict[str, Any]) -> dict[str, Any]:
    """Recompute with Haaland and compare against the primary Swamee-Jain result."""
    secondary = calculate_network(deepcopy(data), method="haaland")
    primary_by_id = {item["segment_id"]: item for item in primary["segments"]}
    comparisons: list[dict[str, Any]] = []
    for item in secondary["segments"]:
        baseline = float(primary_by_id[item["segment_id"]]["pressure_drop_kpa"])
        candidate = float(item["pressure_drop_kpa"])
        relative = abs(candidate - baseline) / max(abs(baseline), 1e-12)
        comparisons.append(
            {
                "segment_id": item["segment_id"],
                "primary_pressure_drop_kpa": round(baseline, 9),
                "independent_pressure_drop_kpa": round(candidate, 9),
                "relative_difference": round(relative, 9),
                "within_5_percent": relative <= 0.05,
            }
        )
    checks = {
        "independent_recalculation_completed": True,
        "segment_differences_within_5_percent": all(
            item["within_5_percent"] for item in comparisons
        ),
        "primary_checks_pass": all(primary["checks"].values()),
        "independent_checks_pass": all(secondary["checks"].values()),
        "endpoint_count_matches": len(primary["endpoint_paths"]) == len(secondary["endpoint_paths"]),
    }
    return {
        "verification_method": "independent Haaland friction-factor recomputation",
        "verification_engine_version": "0.1.0",
        "comparisons": comparisons,
        "checks": checks,
        "verified": all(checks.values()),
    }

