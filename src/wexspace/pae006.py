"""Bounded deterministic PAE-006 motive-air sensitivity micro-study.

The arithmetic in this module is deliberately independent of model prose.  It
accepts only the user-controlled R19 analytical basis, creates the required
12-point study artifacts, and provides a second formulation for independent
verification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import struct
import threading
import uuid
import zlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STUDY_ID = "PAE006-FRESH-MOTIVE-AIR-SENSITIVITY-R01"
TOOL_NAME = "pae006_fresh_motive_air_sensitivity"
VERIFICATION_TOOL_NAME = "independently_verify_pae006_study"

REQUIRED_INPUT = {
    "study_id": STUDY_ID,
    "equipment_model": "PAE-006",
    "pressure_gauge_bar": [4.0, 5.0, 6.0, 7.0],
    "nozzle_throat_diameter_mm": [1.4, 1.6, 1.8],
    "motive_air_supply_pipe_id_mm": 6.0,
    "discharge_coefficient": 0.9,
    "gamma": 1.4,
    "gas_constant_j_kg_k": 287.05,
    "stagnation_temperature_k": 293.15,
    "atmospheric_backpressure_pa_abs": 101325.0,
    "normal_reference_temperature_k": 273.15,
    "normal_reference_pressure_pa_abs": 101325.0,
}

REQUIRED_FILENAMES = (
    "PAE006_FRESH_SENSITIVITY_R01.json",
    "PAE006_FRESH_SENSITIVITY_R01.csv",
    "PAE006_FRESH_AIR_CONSUMPTION_CURVE_R01.png",
    "PAE006_FRESH_CHOKING_CHECK_R01.json",
    "PAE006_FRESH_ENGINEERING_CONCLUSION_R01.md",
)
VERIFICATION_FILENAME = "PAE006_FRESH_INDEPENDENT_VERIFICATION_R01.json"
ADK_EVIDENCE_FILENAME = "PAE006_FRESH_ADK_EXECUTION_EVIDENCE_R01.json"
GATE_FILENAME = "PAE006_R03_GOOGLE_STACK_GATE_R01.json"
MANIFEST_FILENAME = "PAE006_FRESH_SHA256SUMS_R01.txt"

_CACHE_LOCK = threading.Lock()
_RUN_CACHE: dict[str, dict[str, Any]] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decode_input(input_json: str) -> dict[str, Any]:
    value = json.loads(input_json)
    if not isinstance(value, dict):
        raise ValueError("input_json must decode to an object")
    errors = validate_pae006_input(value)
    if errors:
        raise ValueError("; ".join(errors))
    return value


def _same_number(actual: Any, expected: float) -> bool:
    return isinstance(actual, (int, float)) and math.isclose(
        float(actual), expected, rel_tol=0.0, abs_tol=1e-12
    )


def _same_number_list(actual: Any, expected: list[float]) -> bool:
    return (
        isinstance(actual, list)
        and len(actual) == len(expected)
        and all(_same_number(item, target) for item, target in zip(actual, expected))
    )


def validate_pae006_input(data: dict[str, Any]) -> list[str]:
    """Fail closed unless the exact controlled R19 basis is supplied."""
    if not isinstance(data, dict):
        return ["input must be an object"]
    errors: list[str] = []
    allowed_keys = set(REQUIRED_INPUT) | {"context_sources", "prior_work_boundary"}
    unknown = sorted(set(data) - allowed_keys)
    if unknown:
        errors.append("unsupported input keys: " + ", ".join(unknown))
    for key, expected in REQUIRED_INPUT.items():
        if key not in data:
            errors.append(f"{key} is required")
            continue
        actual = data[key]
        if isinstance(expected, list):
            if not _same_number_list(actual, expected):
                errors.append(f"{key} must equal the controlled R19 matrix {expected}")
        elif isinstance(expected, float):
            if not _same_number(actual, expected):
                errors.append(f"{key} must equal the controlled R19 value {expected}")
        elif actual != expected:
            errors.append(f"{key} must equal {expected!r}")
    raw_sources = data.get("context_sources")
    if raw_sources is not None:
        if not isinstance(raw_sources, list) or not raw_sources:
            errors.append("context_sources must be a non-empty array when provided")
        else:
            for index, source in enumerate(raw_sources):
                if not isinstance(source, dict):
                    errors.append(f"context_sources[{index}] must be an object")
                    continue
                if source.get("family") != "PAE006_CONTROLLED_MICRO_STUDY_R19":
                    errors.append(f"context_sources[{index}].family is not R19-allowlisted")
                for flag in ("authority", "relevance", "scope_compatibility"):
                    if source.get(flag) is not True:
                        errors.append(f"context_sources[{index}].{flag} must be true")
    return errors


def govern_pae006_study_request(goal: str, input_json: str) -> dict[str, Any]:
    """Validate the exact study authority and route to the IEW specialist."""
    try:
        value = json.loads(input_json)
    except json.JSONDecodeError as exc:
        return {
            "route": "BLOCK",
            "validation_errors": [f"invalid JSON: {exc.msg}"],
            "goal_allowed": False,
        }
    if not isinstance(value, dict):
        return {
            "route": "BLOCK",
            "validation_errors": ["input_json must decode to an object"],
            "goal_allowed": False,
        }
    goal_allowed = goal.strip() == "Execute PAE-006 fresh motive-air sensitivity study"
    errors = validate_pae006_input(value)
    if not goal_allowed:
        errors.append("goal is outside the bounded R19 PAE-006 authority")
    return {
        "route": "iew_engineering_specialist" if not errors else "BLOCK",
        "goal_allowed": goal_allowed,
        "validation_errors": errors,
        "study_id": value.get("study_id"),
        "input_sha256": canonical_sha256(value),
        "allowed_tool": TOOL_NAME,
        "release_authority": "HUMAN_REVIEW_ONLY",
        "secret_values_logged": False,
    }


def _critical_pressure_ratio(gamma: float) -> float:
    return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))


def _primary_mass_flow(
    *,
    cd: float,
    area_m2: float,
    p0_pa_abs: float,
    t0_k: float,
    gamma: float,
    gas_constant: float,
    backpressure_ratio: float,
) -> tuple[float, bool]:
    critical = _critical_pressure_ratio(gamma)
    choked = backpressure_ratio <= critical
    if choked:
        flow_factor = math.sqrt(
            gamma / gas_constant
            * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (gamma - 1.0))
        )
    else:
        flow_factor = math.sqrt(
            (2.0 * gamma) / (gas_constant * (gamma - 1.0))
            * (
                backpressure_ratio ** (2.0 / gamma)
                - backpressure_ratio ** ((gamma + 1.0) / gamma)
            )
        )
    return cd * area_m2 * p0_pa_abs / math.sqrt(t0_k) * flow_factor, choked


def _calculate_matrix(data: dict[str, Any]) -> dict[str, Any]:
    gamma = float(data["gamma"])
    gas_constant = float(data["gas_constant_j_kg_k"])
    t0_k = float(data["stagnation_temperature_k"])
    p_back = float(data["atmospheric_backpressure_pa_abs"])
    cd = float(data["discharge_coefficient"])
    normal_density = float(data["normal_reference_pressure_pa_abs"]) / (
        gas_constant * float(data["normal_reference_temperature_k"])
    )
    critical = _critical_pressure_ratio(gamma)
    supply_area = math.pi * (float(data["motive_air_supply_pipe_id_mm"]) / 1000.0) ** 2 / 4.0
    points: list[dict[str, Any]] = []
    for pressure_bar_g in data["pressure_gauge_bar"]:
        p0_pa_abs = p_back + float(pressure_bar_g) * 100000.0
        backpressure_ratio = p_back / p0_pa_abs
        for throat_mm in data["nozzle_throat_diameter_mm"]:
            area_m2 = math.pi * (float(throat_mm) / 1000.0) ** 2 / 4.0
            mass_flow_kg_s, choked = _primary_mass_flow(
                cd=cd,
                area_m2=area_m2,
                p0_pa_abs=p0_pa_abs,
                t0_k=t0_k,
                gamma=gamma,
                gas_constant=gas_constant,
                backpressure_ratio=backpressure_ratio,
            )
            points.append(
                {
                    "pressure_gauge_bar": float(pressure_bar_g),
                    "stagnation_pressure_pa_abs": round(p0_pa_abs, 6),
                    "throat_diameter_mm": float(throat_mm),
                    "throat_area_m2": round(area_m2, 15),
                    "supply_pipe_id_mm": float(data["motive_air_supply_pipe_id_mm"]),
                    "throat_to_supply_area_ratio": round(area_m2 / supply_area, 12),
                    "atmospheric_backpressure_pa_abs": round(p_back, 6),
                    "backpressure_to_stagnation_ratio": round(backpressure_ratio, 12),
                    "critical_pressure_ratio": round(critical, 12),
                    "choked": choked,
                    "flow_regime": "CHOKED" if choked else "SUBCRITICAL",
                    "mass_flow_kg_s": round(mass_flow_kg_s, 12),
                    "mass_flow_kg_h": round(mass_flow_kg_s * 3600.0, 9),
                    "normal_air_consumption_nm3_h": round(
                        mass_flow_kg_s * 3600.0 / normal_density, 9
                    ),
                }
            )
    mass_values = [point["mass_flow_kg_s"] for point in points]
    normal_values = [point["normal_air_consumption_nm3_h"] for point in points]
    return {
        "point_count": len(points),
        "critical_pressure_ratio": round(critical, 12),
        "normal_air_density_kg_m3": round(normal_density, 12),
        "matrix": points,
        "summary": {
            "all_points_choked": all(point["choked"] for point in points),
            "choked_point_count": sum(1 for point in points if point["choked"]),
            "mass_flow_min_kg_s": min(mass_values),
            "mass_flow_max_kg_s": max(mass_values),
            "normal_air_consumption_min_nm3_h": min(normal_values),
            "normal_air_consumption_max_nm3_h": max(normal_values),
            "pressure_4_to_7_bar_g_fixed_throat_ratio": round(
                (p_back + 700000.0) / (p_back + 400000.0), 12
            ),
            "throat_1_8_to_1_4_mm_fixed_pressure_ratio": round((1.8 / 1.4) ** 2, 12),
        },
    }


_FONT = {
    " ": ("00000",) * 7,
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "/": ("00001", "00010", "00100", "01000", "10000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00001", "00001", "00001", "00001", "10001", "10001", "01110"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


class _Canvas:
    def __init__(self, width: int, height: int, color: tuple[int, int, int]):
        self.width = width
        self.height = height
        self.pixels = bytearray(color * (width * height))

    def pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset : offset + 3] = bytes(color)

    def line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
        thickness: int = 1,
    ) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            radius = max(0, thickness // 2)
            for oy in range(-radius, radius + 1):
                for ox in range(-radius, radius + 1):
                    self.pixel(x0 + ox, y0 + oy, color)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def rectangle(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
        *,
        fill: bool = False,
    ) -> None:
        if fill:
            for y in range(y0, y1 + 1):
                self.line(x0, y, x1, y, color)
        else:
            self.line(x0, y0, x1, y0, color)
            self.line(x1, y0, x1, y1, color)
            self.line(x1, y1, x0, y1, color)
            self.line(x0, y1, x0, y0, color)

    def text(
        self,
        x: int,
        y: int,
        value: str,
        color: tuple[int, int, int],
        scale: int = 2,
    ) -> None:
        cursor = x
        for character in value.upper():
            glyph = _FONT.get(character, _FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        self.rectangle(
                            cursor + gx * scale,
                            y + gy * scale,
                            cursor + (gx + 1) * scale - 1,
                            y + (gy + 1) * scale - 1,
                            color,
                            fill=True,
                        )
            cursor += 6 * scale

    def save_png(self, path: Path) -> None:
        rows = bytearray()
        row_size = self.width * 3
        for y in range(self.height):
            rows.append(0)
            start = y * row_size
            rows.extend(self.pixels[start : start + row_size])

        def chunk(kind: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            )

        payload = b"\x89PNG\r\n\x1a\n"
        payload += chunk(
            b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        )
        payload += chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        payload += chunk(b"IEND", b"")
        path.write_bytes(payload)


def _write_curve_png(path: Path, points: list[dict[str, Any]]) -> None:
    width, height = 1200, 720
    canvas = _Canvas(width, height, (248, 250, 252))
    ink = (20, 35, 55)
    grid = (205, 214, 224)
    plot_fill = (255, 255, 255)
    x0, y0, x1, y1 = 105, 95, 1080, 590
    canvas.rectangle(x0, y0, x1, y1, plot_fill, fill=True)
    canvas.text(92, 28, "PAE-006 NORMAL AIR CONSUMPTION", ink, scale=4)
    values = [float(point["normal_air_consumption_nm3_h"]) for point in points]
    y_min = math.floor(min(values) * 0.9)
    y_max = math.ceil(max(values) * 1.08)
    if y_max <= y_min:
        y_max = y_min + 1

    def x_px(value: float) -> int:
        return int(round(x0 + (value - 4.0) / 3.0 * (x1 - x0)))

    def y_px(value: float) -> int:
        return int(round(y1 - (value - y_min) / (y_max - y_min) * (y1 - y0)))

    for index in range(6):
        value = y_min + (y_max - y_min) * index / 5.0
        py = y_px(value)
        canvas.line(x0, py, x1, py, grid)
        canvas.text(25, py - 7, f"{value:.1f}", ink, scale=2)
    for pressure in (4.0, 5.0, 6.0, 7.0):
        px = x_px(pressure)
        canvas.line(px, y0, px, y1, grid)
        canvas.text(px - 6, y1 + 15, f"{pressure:.0f}", ink, scale=2)
    canvas.rectangle(x0, y0, x1, y1, ink)
    canvas.text(392, 635, "MOTIVE PRESSURE BAR(G)", ink, scale=3)
    canvas.text(25, 66, "NORMAL AIR NM3/H", ink, scale=2)

    colors = {1.4: (0, 124, 137), 1.6: (44, 95, 170), 1.8: (222, 122, 0)}
    for throat in (1.4, 1.6, 1.8):
        series = sorted(
            (
                point
                for point in points
                if math.isclose(float(point["throat_diameter_mm"]), throat)
            ),
            key=lambda item: float(item["pressure_gauge_bar"]),
        )
        color = colors[throat]
        for left, right in zip(series, series[1:]):
            canvas.line(
                x_px(float(left["pressure_gauge_bar"])),
                y_px(float(left["normal_air_consumption_nm3_h"])),
                x_px(float(right["pressure_gauge_bar"])),
                y_px(float(right["normal_air_consumption_nm3_h"])),
                color,
                thickness=5,
            )
        for point in series:
            px = x_px(float(point["pressure_gauge_bar"]))
            py = y_px(float(point["normal_air_consumption_nm3_h"]))
            canvas.rectangle(px - 5, py - 5, px + 5, py + 5, color, fill=True)

    legend_x, legend_y = 820, 115
    canvas.rectangle(legend_x - 20, legend_y - 20, 1055, 220, (238, 242, 247), fill=True)
    canvas.rectangle(legend_x - 20, legend_y - 20, 1055, 220, grid)
    for index, throat in enumerate((1.4, 1.6, 1.8)):
        py = legend_y + index * 34
        canvas.line(legend_x, py + 7, legend_x + 50, py + 7, colors[throat], thickness=5)
        canvas.text(legend_x + 68, py, f"{throat:.1f} MM THROAT", ink, scale=2)
    canvas.text(
        118,
        686,
        "ATMOSPHERIC BACKPRESSURE - ALL 12 OPERATING POINTS CHOKED",
        (47, 88, 75),
        scale=2,
    )
    canvas.save_png(path)


def _safe_run_directory(root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    run_dir = root / STUDY_ID / f"{timestamp}-{suffix}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, points: list[dict[str, Any]]) -> None:
    fields = [
        "pressure_gauge_bar",
        "stagnation_pressure_pa_abs",
        "throat_diameter_mm",
        "throat_area_m2",
        "supply_pipe_id_mm",
        "throat_to_supply_area_ratio",
        "atmospheric_backpressure_pa_abs",
        "backpressure_to_stagnation_ratio",
        "critical_pressure_ratio",
        "choked",
        "flow_regime",
        "mass_flow_kg_s",
        "mass_flow_kg_h",
        "normal_air_consumption_nm3_h",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(points)


def _write_conclusion(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    lines = [
        f"# {STUDY_ID}",
        "",
        "## Engineering conclusion",
        "",
        f"All {result['point_count']} controlled operating points are analytically choked at "
        "101325 Pa absolute atmospheric backpressure.",
        "",
        f"- Critical pressure ratio: `{result['critical_pressure_ratio']:.12f}`.",
        f"- Mass-flow range: `{summary['mass_flow_min_kg_s']:.12f}` to "
        f"`{summary['mass_flow_max_kg_s']:.12f}` kg/s.",
        f"- Normal-air range: `{summary['normal_air_consumption_min_nm3_h']:.9f}` to "
        f"`{summary['normal_air_consumption_max_nm3_h']:.9f}` Nm3/h at 0 °C and "
        "1.01325 bar absolute.",
        f"- Raising motive pressure from 4 to 7 bar(g) multiplies flow by "
        f"`{summary['pressure_4_to_7_bar_g_fixed_throat_ratio']:.12f}` at fixed throat.",
        f"- Raising throat diameter from 1.4 to 1.8 mm multiplies flow by "
        f"`{summary['throat_1_8_to_1_4_mm_fixed_pressure_ratio']:.12f}` at fixed pressure.",
        "",
        "The 6.00 mm motive-air supply ID is retained in every point as controlled geometry. "
        "This bounded sensitivity study treats the stated motive pressure as the ejector-inlet "
        "stagnation pressure under flow; it does not add an unprovided upstream line-loss model.",
        "",
        "These are analytical motive-air estimates, not tested performance or a product rating. "
        "The discharge coefficient 0.90 is a controlled working assumption pending nozzle flow "
        "calibration.",
        "",
        "The PAE-006 basis is pre-existing user-controlled engineering context. The isolated "
        "R19 adapter, fresh recalculation, generated artifacts, and Google-stack execution "
        "evidence belong to this fresh run.",
        "",
        "Release remains blocked pending accountable human review.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _refresh_manifest(run: dict[str, Any]) -> None:
    run_dir = Path(run["run_directory"])
    manifest_path = run_dir / MANIFEST_FILENAME
    files = sorted(path for path in run_dir.iterdir() if path.is_file() and path != manifest_path)
    lines: list[str] = []
    artifacts: dict[str, dict[str, Any]] = {}
    for path in files:
        sha256 = _file_sha256(path)
        lines.append(f"{sha256}  {path.name}")
        artifacts[path.name] = {
            "path": str(path),
            "sha256": sha256,
            "size_bytes": path.stat().st_size,
        }
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    artifacts[MANIFEST_FILENAME] = {
        "path": str(manifest_path),
        "sha256": _file_sha256(manifest_path),
        "size_bytes": manifest_path.stat().st_size,
    }
    run["artifacts"] = artifacts
    run["sha256_manifest"] = artifacts[MANIFEST_FILENAME]


def _cache_key(data: dict[str, Any]) -> str:
    return canonical_sha256(data)


def pae006_fresh_motive_air_sensitivity(input_json: str) -> dict[str, Any]:
    """Calculate the fresh 12-point matrix and create required artifacts."""
    data = _decode_input(input_json)
    generated_at = _utc_now()
    result = _calculate_matrix(data)
    root = Path(os.getenv("WEXSPACE_PAE_OUTPUT_ROOT", "/tmp/wexspace/pae006"))
    run_dir = _safe_run_directory(root)
    input_sha256 = _cache_key(data)
    result_document = {
        "schema_version": "1.0",
        "study_id": STUDY_ID,
        "generated_at_utc": generated_at,
        "fresh_recalculation": True,
        "calculation_source": "deterministic_python_tool",
        "tool": TOOL_NAME,
        "input_sha256": input_sha256,
        "controlled_basis": data,
        "analytical_method": {
            "mass_flow": "compressible isentropic orifice equation with explicit choking branch",
            "choking_criterion": "P_back/P0 <= (2/(gamma+1))^(gamma/(gamma-1))",
            "normal_reference": "0 degC and 1.01325 bar absolute",
            "motive_pressure_interpretation": "ejector-inlet stagnation pressure under flow",
        },
        **result,
        "workflow_release_state": "AWAITING_HUMAN_REVIEW",
        "release_performed": False,
    }
    sensitivity_path = run_dir / REQUIRED_FILENAMES[0]
    csv_path = run_dir / REQUIRED_FILENAMES[1]
    curve_path = run_dir / REQUIRED_FILENAMES[2]
    choking_path = run_dir / REQUIRED_FILENAMES[3]
    conclusion_path = run_dir / REQUIRED_FILENAMES[4]
    _write_json(sensitivity_path, result_document)
    _write_csv(csv_path, result["matrix"])
    _write_curve_png(curve_path, result["matrix"])
    choking_document = {
        "schema_version": "1.0",
        "study_id": STUDY_ID,
        "generated_at_utc": generated_at,
        "choking_criterion": "P_back/P0 <= critical_pressure_ratio",
        "critical_pressure_ratio": result["critical_pressure_ratio"],
        "atmospheric_backpressure_pa_abs": data["atmospheric_backpressure_pa_abs"],
        "point_count": result["point_count"],
        "all_points_choked": result["summary"]["all_points_choked"],
        "points": [
            {
                key: point[key]
                for key in (
                    "pressure_gauge_bar",
                    "stagnation_pressure_pa_abs",
                    "throat_diameter_mm",
                    "backpressure_to_stagnation_ratio",
                    "critical_pressure_ratio",
                    "choked",
                    "flow_regime",
                )
            }
            for point in result["matrix"]
        ],
    }
    _write_json(choking_path, choking_document)
    _write_conclusion(conclusion_path, result)
    run = {
        "schema_version": "1.0",
        "study_id": STUDY_ID,
        "run_id": run_dir.name,
        "run_directory": str(run_dir),
        "generated_at_utc": generated_at,
        "input": data,
        "input_sha256": input_sha256,
        "result": result,
        "primary_result_document": result_document,
        "verification": None,
        "source": "deterministic_python_tool",
        "tool": TOOL_NAME,
        "workflow_state": "ENGINEERING_COMPLETE_VERIFICATION_REQUIRED",
        "release_performed": False,
    }
    _refresh_manifest(run)
    with _CACHE_LOCK:
        _RUN_CACHE[input_sha256] = run
    return {
        "study_id": STUDY_ID,
        "run_id": run["run_id"],
        "generated_at_utc": generated_at,
        "input_sha256": input_sha256,
        "point_count": result["point_count"],
        "matrix": result["matrix"],
        "summary": result["summary"],
        "all_points_choked": result["summary"]["all_points_choked"],
        "artifacts": deepcopy(run["artifacts"]),
        "source": "deterministic_python_tool",
        "workflow_state": run["workflow_state"],
        "release_performed": False,
    }


def _independent_point(data: dict[str, Any], point: dict[str, Any]) -> dict[str, Any]:
    gamma = float(data["gamma"])
    gas_constant = float(data["gas_constant_j_kg_k"])
    t0_k = float(data["stagnation_temperature_k"])
    p0 = float(point["stagnation_pressure_pa_abs"])
    p_back = float(data["atmospheric_backpressure_pa_abs"])
    ratio = p_back / p0
    critical = _critical_pressure_ratio(gamma)
    choked = ratio <= critical
    if not choked:
        raise ValueError(
            "independent verifier is intentionally bounded to the controlled choked matrix"
        )
    t_star = t0_k * 2.0 / (gamma + 1.0)
    p_star = p0 * critical
    rho_star = p_star / (gas_constant * t_star)
    sonic_speed = math.sqrt(gamma * gas_constant * t_star)
    area = math.pi * (float(point["throat_diameter_mm"]) / 1000.0) ** 2 / 4.0
    mass_flow = float(data["discharge_coefficient"]) * area * rho_star * sonic_speed
    normal_density = float(data["normal_reference_pressure_pa_abs"]) / (
        gas_constant * float(data["normal_reference_temperature_k"])
    )
    return {
        "pressure_gauge_bar": point["pressure_gauge_bar"],
        "throat_diameter_mm": point["throat_diameter_mm"],
        "critical_temperature_k": t_star,
        "critical_pressure_pa_abs": p_star,
        "critical_density_kg_m3": rho_star,
        "critical_sonic_speed_m_s": sonic_speed,
        "mass_flow_kg_s": mass_flow,
        "normal_air_consumption_nm3_h": mass_flow * 3600.0 / normal_density,
        "choked": choked,
    }


def independently_verify_pae006_study(input_json: str) -> dict[str, Any]:
    """Independently recompute by critical-state density times sonic velocity."""
    data = _decode_input(input_json)
    key = _cache_key(data)
    with _CACHE_LOCK:
        cached = _RUN_CACHE.get(key)
    if cached is None:
        raise ValueError("primary PAE-006 tool result is absent; verification fails closed")
    primary_points = cached["result"]["matrix"]
    comparisons: list[dict[str, Any]] = []
    for primary in primary_points:
        independent = _independent_point(data, primary)
        mass_relative = abs(
            independent["mass_flow_kg_s"] - float(primary["mass_flow_kg_s"])
        ) / max(abs(float(primary["mass_flow_kg_s"])), 1e-15)
        normal_relative = abs(
            independent["normal_air_consumption_nm3_h"]
            - float(primary["normal_air_consumption_nm3_h"])
        ) / max(abs(float(primary["normal_air_consumption_nm3_h"])), 1e-15)
        comparisons.append(
            {
                "pressure_gauge_bar": primary["pressure_gauge_bar"],
                "throat_diameter_mm": primary["throat_diameter_mm"],
                "primary_mass_flow_kg_s": primary["mass_flow_kg_s"],
                "independent_mass_flow_kg_s": round(independent["mass_flow_kg_s"], 12),
                "mass_flow_relative_difference": mass_relative,
                "primary_normal_air_consumption_nm3_h": primary[
                    "normal_air_consumption_nm3_h"
                ],
                "independent_normal_air_consumption_nm3_h": round(
                    independent["normal_air_consumption_nm3_h"], 9
                ),
                "normal_air_relative_difference": normal_relative,
                "choking_matches": independent["choked"] is primary["choked"],
                "within_tolerance": mass_relative <= 1e-8 and normal_relative <= 1e-8,
            }
        )
    required_present = all(
        (Path(cached["run_directory"]) / name).is_file()
        for name in REQUIRED_FILENAMES
    )
    checks = {
        "independent_critical_state_recalculation_completed": len(comparisons) == 12,
        "all_mass_flow_values_within_relative_tolerance_1e_8": all(
            item["within_tolerance"] for item in comparisons
        ),
        "all_choking_classifications_match": all(
            item["choking_matches"] for item in comparisons
        ),
        "all_12_primary_points_choked": all(point["choked"] for point in primary_points),
        "required_fresh_artifacts_present": required_present,
    }
    verification = {
        "schema_version": "1.0",
        "study_id": STUDY_ID,
        "verified_at_utc": _utc_now(),
        "verification_source": "independent_deterministic_python_tool",
        "verification_method": "critical-state density multiplied by sonic velocity",
        "primary_tool": TOOL_NAME,
        "verification_tool": VERIFICATION_TOOL_NAME,
        "point_count": len(comparisons),
        "comparisons": comparisons,
        "checks": checks,
        "verified": all(checks.values()),
        "release_performed": False,
    }
    verification_path = Path(cached["run_directory"]) / VERIFICATION_FILENAME
    _write_json(verification_path, verification)
    cached["verification"] = verification
    cached["workflow_state"] = (
        "AWAITING_HUMAN_REVIEW" if verification["verified"] else "REJECTED_VERIFICATION"
    )
    _refresh_manifest(cached)
    with _CACHE_LOCK:
        _RUN_CACHE[key] = cached
    return {
        **verification,
        "workflow_state": cached["workflow_state"],
        "artifacts": deepcopy(cached["artifacts"]),
    }


def get_cached_pae006_run(payload: dict[str, Any]) -> dict[str, Any] | None:
    with _CACHE_LOCK:
        run = _RUN_CACHE.get(_cache_key(payload))
        return deepcopy(run) if run is not None else None


def finalize_google_stack_evidence(
    payload: dict[str, Any], execution_evidence: dict[str, Any]
) -> dict[str, Any]:
    """Attach the authentic ADK trace/gate record and refresh the manifest."""
    key = _cache_key(payload)
    with _CACHE_LOCK:
        cached = _RUN_CACHE.get(key)
    if cached is None:
        raise ValueError("cannot finalize Google evidence without a deterministic tool run")
    run_dir = Path(cached["run_directory"])
    _write_json(run_dir / ADK_EVIDENCE_FILENAME, execution_evidence)
    gate = {
        "schema_version": "1.0",
        "gate_id": "PAE_R03_GOOGLE_STACK_GATE",
        "study_id": STUDY_ID,
        "evaluated_at_utc": _utc_now(),
        "checks": {
            "google_adk_actual_invocation": execution_evidence.get(
                "google_agent_framework_used"
            )
            is True,
            "gemini_3_7_flash_actual_invocation": execution_evidence.get(
                "gemini_3_5_plus_used"
            )
            is True
            and execution_evidence.get("actual_model") == "gemini-3.7-flash",
            "google_cloud_execution_proof": execution_evidence.get(
                "google_cloud_infrastructure_used"
            )
            is True,
            "wexspace_governing_agent": execution_evidence.get(
                "governing_agent_invoked"
            )
            is True,
            "iew_delegation": execution_evidence.get("iew_specialist_invoked") is True,
            "fresh_deterministic_pae_study": execution_evidence.get(
                "pae_deterministic_tool_invoked"
            )
            is True
            and cached["result"]["point_count"] == 12,
            "verification_specialist": execution_evidence.get(
                "verification_specialist_invoked"
            )
            is True
            and bool(cached.get("verification", {}).get("verified")),
            "awaiting_human_review": execution_evidence.get("workflow_state")
            == "AWAITING_HUMAN_REVIEW"
            and execution_evidence.get("release_performed") is False,
        },
        "release_performed": False,
    }
    gate["status"] = "PASS" if all(gate["checks"].values()) else "FAIL"
    _write_json(run_dir / GATE_FILENAME, gate)
    cached["google_stack_evidence"] = execution_evidence
    cached["google_stack_gate"] = gate
    _refresh_manifest(cached)
    with _CACHE_LOCK:
        _RUN_CACHE[key] = cached
    return deepcopy(cached)


def artifact_manifest_is_valid(run: dict[str, Any]) -> bool:
    artifacts = run.get("artifacts", {})
    required = set(REQUIRED_FILENAMES) | {
        VERIFICATION_FILENAME,
        ADK_EVIDENCE_FILENAME,
        GATE_FILENAME,
        MANIFEST_FILENAME,
    }
    if not required.issubset(artifacts):
        return False
    manifest_path = Path(artifacts[MANIFEST_FILENAME]["path"])
    if not manifest_path.is_file():
        return False
    seen: dict[str, str] = {}
    pattern = re.compile(r"^([0-9a-f]{64})  (.+)$")
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if not match:
            return False
        seen[match.group(2)] = match.group(1)
    for name in required - {MANIFEST_FILENAME}:
        path = Path(artifacts[name]["path"])
        if not path.is_file() or seen.get(name) != _file_sha256(path):
            return False
    return artifacts[MANIFEST_FILENAME]["sha256"] == _file_sha256(manifest_path)
