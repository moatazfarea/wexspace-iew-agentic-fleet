#!/usr/bin/env python3
"""Build the judge-optimized R02 video without altering the R01 fallback."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from render_competition_video import (
    AMBER,
    BLUE,
    GREEN,
    PURPLE,
    Slide,
    render_slide,
)


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
OUTPUT = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R02.mp4"
SUBTITLES = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R02.srt"
THUMBNAIL = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R02_THUMBNAIL.png"
LIVE_CLIP = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R02_LIVE.mp4"
PROOF_CLIP = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R02_CLOUD_PROOF.mp4"
LIVE_TRANSCRIPT = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R02_LIVE_TRANSCRIPT.txt"
PROOF_TRANSCRIPT = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R02_CLOUD_PROOF_TRANSCRIPT.txt"
METADATA = DEMO / "YOUTUBE_PUBLICATION_METADATA_R02.md"


@dataclass(frozen=True)
class Still:
    duration: int
    slide: Slide
    caption: str


STILLS_BEFORE = (
    Still(
        12,
        Slide(
            12,
            "LIVE PROFESSIONAL EXECUTION",
            "WEXSPACE AI coordinates bounded professional work",
            "One real synthetic engineering workflow—from governed request to accountable human release.",
            (
                "ONE SYNTHETIC COOLING-WATER GOAL",
                "THREE BOUNDED AGENT RESPONSIBILITIES",
                "DETERMINISTIC ENGINEERING + INDEPENDENT CHECK",
                "ACCOUNTABLE HUMAN RELEASE",
            ),
            GREEN,
            "hero",
        ),
        "WEXSPACE AI coordinates bounded professional responsibilities around one real engineering task.",
    ),
    Still(
        16,
        Slide(
            16,
            "THE PROBLEM",
            "Engineering needs more than an answer",
            "High-consequence work needs reproducibility, independent checking, provenance, and accountable release.",
            (
                "Complete inputs — never guessed",
                "Deterministic equations — not model arithmetic",
                "Independent verification — separate responsibility",
                "Human approval — no autonomous release",
            ),
            AMBER,
            "cards",
        ),
        "Engineering inputs must be complete, calculations reproducible, checks independent, and release accountable.",
    ),
    Still(
        16,
        Slide(
            16,
            "WHY A GOVERNED FLEET",
            "Three bounded agents + accountable human release",
            "The model coordinates professional work; deterministic tools remain the numerical authority.",
            (
                "WEXSPACE Governing Agent — context · scope · policy · routing",
                "IEW Engineering Specialist — deterministic hydraulic calculation",
                "Verification / Evidence Specialist — independent recomputation",
                "Accountable reviewer — the only release authority",
            ),
            BLUE,
            "flow",
        ),
        "The governing agent validates scope and routes the task. Separate specialists calculate and verify; a human controls release.",
    ),
)


STILLS_AFTER_LIVE = (
    Still(
        18,
        Slide(
            18,
            "PERSISTENCE + FORTIFIED CONTROL",
            "Resume the same governed workflow in a fresh process",
            "Application-level persistent state is proven locally; Cloud Run cross-instance database durability is not claimed.",
            (
                "PAUSE  →  verification state persisted",
                "REOPEN  →  same workflow identity",
                "RESUME  →  independent check completed",
                "STOP  →  AWAITING_HUMAN_REVIEW",
            ),
            PURPLE,
            "timeline",
        ),
        "The same workflow can pause, reopen, and resume without losing its verification or human-release boundary.",
    ),
)


STILLS_AFTER_PROOF = (
    Still(
        15,
        Slide(
            15,
            "PUBLIC + REPRODUCIBLE",
            "One judge-accessible repository, explicit provenance",
            "Runtime identity remains mapped when later submission commits change documentation or media only.",
            (
                "github.com/moatazfarea/wexspace-iew-agentic-fleet",
                "deployed commit  da70a9b7bb08280f9c5d3c450e2171f28dea6c96",
                "deployed tree    6c572860fa041efde6b8bad8a19ed05d54465582",
                "README · architecture · tests · evidence · disclosures",
            ),
            BLUE,
            "repository",
        ),
        "The public repository preserves setup, architecture, tests, evidence, disclosures, and deployed-runtime provenance.",
    ),
    Still(
        32,
        Slide(
            32,
            "WHAT THE JUDGE JUST WATCHED",
            "Professional execution with bounded responsibility",
            "IEW is the first deeply implemented domain inside the broader WEXSPACE architecture.",
            (
                "Governed — explicit scope, policy, authority, and routing",
                "Reproducible — deterministic equations and persisted state",
                "Independently verified — separate method and evidence hashes",
                "Human-accountable — autonomous work, controlled release",
            ),
            GREEN,
            "cards",
        ),
        "WEXSPACE makes professional agent execution bounded, reproducible, independently verifiable, and human-accountable.",
    ),
    Still(
        10,
        Slide(
            10,
            "WEXSPACE AI",
            "Governed expert-agent fleets",
            "For high-consequence professional work · Bounded · Reproducible · Independently verified · Human-accountable",
            ("IEW: first deeply implemented professional domain.",),
            GREEN,
            "final",
        ),
        "WEXSPACE AI. IEW is the first deeply implemented professional domain.",
    ),
)


def duration(path: Path) -> float:
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        text=True,
    )
    return float(raw.strip())


def srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, rem = divmod(milliseconds, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def render_still(item: Still, index: int, target: Path) -> None:
    frame = render_slide(item.slide, index)
    if index == 1:
        frame.save(THUMBNAIL, optimize=True)
    frame_path = target.with_suffix(".png")
    frame.save(frame_path, optimize=True)
    fade_out = max(0, item.duration - 0.3)
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-framerate", "30", "-i", str(frame_path),
            "-t", str(item.duration),
            "-vf", f"fade=t=in:st=0:d=0.3,fade=t=out:st={fade_out}:d=0.3,format=yuv420p",
            "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "25",
            "-r", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
        ],
        check=True,
    )


def ensure_captures() -> None:
    live_evidence = ROOT / "evidence" / "demo" / "R07_VIDEO_R02_LIVE_RUN_RESULT.json"
    if not LIVE_CLIP.exists() or not LIVE_TRANSCRIPT.exists() or not live_evidence.exists():
        subprocess.run(
            [
                "python3", str(DEMO / "record_terminal_capture.py"), "--mode", "live",
                "--output", str(LIVE_CLIP), "--transcript", str(LIVE_TRANSCRIPT),
            ],
            cwd=ROOT,
            check=True,
        )
    if not PROOF_CLIP.exists() or not PROOF_TRANSCRIPT.exists():
        subprocess.run(
            [
                "python3", str(DEMO / "record_terminal_capture.py"), "--mode", "proof",
                "--output", str(PROOF_CLIP), "--transcript", str(PROOF_TRANSCRIPT),
            ],
            cwd=ROOT,
            check=True,
        )


def write_subtitles(timeline: list[tuple[float, float, str]]) -> None:
    blocks = []
    for index, (start, end, caption) in enumerate(timeline, 1):
        blocks.append(f"{index}\n{srt_time(start)} --> {srt_time(end)}\n{caption}\n")
    SUBTITLES.write_text("\n".join(blocks), encoding="utf-8")


def write_metadata(total: float) -> None:
    video_sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    subtitle_sha = hashlib.sha256(SUBTITLES.read_bytes()).hexdigest()
    METADATA.write_text(
        "# YouTube publication metadata — VIDEO_R02\n\n"
        "## Title\n\n"
        "WEXSPACE AI — Live Governed Engineering Agent Fleet on Google Cloud\n\n"
        "## Description\n\n"
        "Watch WEXSPACE AI execute one continuous neutral synthetic engineering workflow: "
        "the Governing Agent validates scope and routes work, the IEW Engineering Specialist "
        "invokes deterministic hydraulic equations, the Verification / Evidence Specialist "
        "independently recomputes the result, and the workflow stops for accountable human review.\n\n"
        "The deployed successor runs on Google Cloud Run with Google ADK, Vertex AI, "
        "Application Default Credentials, and Gemini 3.7 Flash. The public repository is "
        "https://github.com/moatazfarea/wexspace-iew-agentic-fleet\n\n"
        "All demo data is synthetic and neutral. No secret value or confidential information is shown.\n\n"
        "## Verified artifact\n\n"
        f"- revision: `VIDEO_R02`\n- duration: `{total:.3f}` seconds\n"
        f"- video SHA-256: `{video_sha}`\n- subtitle SHA-256: `{subtitle_sha}`\n"
        "- visibility target: `PUBLIC`\n- final upload: pending authenticated publication\n",
        encoding="utf-8",
    )


def main() -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    ensure_captures()
    live_duration = duration(LIVE_CLIP)
    proof_duration = duration(PROOF_CLIP)
    if not 70 <= live_duration <= 100:
        raise SystemExit(f"live capture must be 70–100 seconds, got {live_duration:.3f}")

    with tempfile.TemporaryDirectory(prefix="wexspace-r02-") as raw:
        temp = Path(raw)
        parts: list[Path] = []
        timeline: list[tuple[float, float, str]] = []
        cursor = 0.0
        slide_number = 1

        for item in STILLS_BEFORE:
            part = temp / f"part-{len(parts):02d}.mp4"
            render_still(item, slide_number, part)
            parts.append(part)
            timeline.append((cursor, cursor + item.duration, item.caption))
            cursor += item.duration
            slide_number += 1

        parts.append(LIVE_CLIP)
        timeline.append(
            (
                cursor,
                cursor + live_duration,
                "Continuous authentic run: governing, specialist delegation, deterministic calculation, independent verification, and the human-release hold.",
            )
        )
        cursor += live_duration

        for item in STILLS_AFTER_LIVE:
            part = temp / f"part-{len(parts):02d}.mp4"
            render_still(item, slide_number, part)
            parts.append(part)
            timeline.append((cursor, cursor + item.duration, item.caption))
            cursor += item.duration
            slide_number += 1

        parts.append(PROOF_CLIP)
        timeline.append(
            (
                cursor,
                cursor + proof_duration,
                "Authentic public-safe Cloud evidence: project, service, revision, live HTTP 200, Vertex AI identity, logs, checks, archive hash, and deployed-source provenance.",
            )
        )
        cursor += proof_duration

        for item in STILLS_AFTER_PROOF:
            part = temp / f"part-{len(parts):02d}.mp4"
            render_still(item, slide_number, part)
            parts.append(part)
            timeline.append((cursor, cursor + item.duration, item.caption))
            cursor += item.duration
            slide_number += 1

        if cursor > 235:
            raise SystemExit(f"R02 exceeds the 3:55 safety cap: {cursor:.3f} seconds")
        concat = temp / "concat.txt"
        concat.write_text("".join(f"file '{part}'\n" for part in parts), encoding="utf-8")
        video_only = temp / "video-only.mp4"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat),
                "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "25",
                "-r", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_only),
            ],
            check=True,
        )
        write_subtitles(timeline)
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(video_only), "-i", str(SUBTITLES),
                "-map", "0:v:0", "-map", "1:0", "-c:v", "copy", "-c:s", "mov_text",
                "-metadata:s:s:0", "language=eng", "-movflags", "+faststart", str(OUTPUT),
            ],
            check=True,
        )
    total = duration(OUTPUT)
    if total > 240:
        raise SystemExit(f"rendered video exceeds four minutes: {total:.3f}")
    write_metadata(total)
    print(json.dumps({"output": str(OUTPUT), "duration": total, "live": live_duration, "proof": proof_duration}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
