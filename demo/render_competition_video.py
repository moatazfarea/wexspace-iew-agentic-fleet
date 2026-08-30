#!/usr/bin/env python3
"""Render the public-safe WEXSPACE competition demo from verified artifacts."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
ARCHITECTURE = ROOT / "architecture" / "architecture_submission.png"
OUTPUT = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R01.mp4"
SUBTITLES = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R01.srt"
THUMBNAIL = DEMO / "WEXSPACE_AI_HACKATHON_DEMO_R01_THUMBNAIL.png"

WIDTH, HEIGHT = 1920, 1080
NAVY = "#101D3A"
BLUE = "#2855D9"
GREEN = "#16845B"
PURPLE = "#7047B8"
AMBER = "#A86100"
INK = "#14213D"
MUTED = "#526079"
PALE = "#F7F9FE"
WHITE = "#FFFFFF"

FONT_ROOT = Path("/usr/share/fonts/truetype/dejavu")
FONT_BOLD = FONT_ROOT / "DejaVuSans-Bold.ttf"
FONT_REGULAR = FONT_ROOT / "DejaVuSans.ttf"
FONT_MONO = FONT_ROOT / "DejaVuSansMono.ttf"


@dataclass(frozen=True)
class Slide:
    duration: int
    kicker: str
    title: str
    subtitle: str
    body: tuple[str, ...]
    accent: str = BLUE
    layout: str = "cards"
    narration: str = ""


SLIDES = (
    Slide(
        15,
        "REAL GOOGLE CLOUD EXECUTION",
        "WEXSPACE AI is live on Cloud Run",
        "Google ADK · Vertex AI · Gemini 3.7 Flash · Application Default Credentials",
        (
            "PROJECT  wexspace-agentic-2026",
            "SERVICE  wexspace-iew-agentic-fleet",
            "REVISION  wexspace-iew-agentic-fleet-00002-9tw",
            "LIVE ADK  HTTP 200  ·  CLOUD GATE PASS  ·  7 / 7",
        ),
        GREEN,
        "hero",
        "This is WEXSPACE AI running on Google Cloud Run: a governed three-agent engineering workflow using Google ADK, Vertex AI, and Gemini 3.7 Flash.",
    ),
    Slide(
        20,
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
        "Industrial engineering work is more than producing an answer. Inputs must be complete, calculations reproducible, checks independent, decisions traceable, and consequential results released by an accountable human.",
    ),
    Slide(
        20,
        "WHY A FLEET, NOT A CHATBOT",
        "Three bounded responsibilities",
        "The model coordinates professional work; deterministic tools remain the numerical authority.",
        (
            "WEXSPACE Governing Agent — policy, context, scope, routing",
            "IEW Engineering Specialist — bounded hydraulic calculation",
            "Verification / Evidence Specialist — independent check and provenance",
            "Accountable reviewer — the only release authority",
        ),
        BLUE,
        "flow",
        "The WEXSPACE Governing Agent controls context, policy, and routing. The IEW Engineering Specialist invokes deterministic equations. The Verification and Evidence Specialist recomputes the result, and a human controls release.",
    ),
    Slide(
        20,
        "IMPLEMENTED ARCHITECTURE",
        "Verified application path and evidence boundaries",
        "Solid paths are implemented; future managed services remain explicitly labeled not implemented.",
        (),
        PURPLE,
        "architecture",
        "The deployed route uses Google ADK and Gemini 3.7 Flash through Vertex AI. Cloud Run hosts the API, while application controls preserve scope, state, evidence, and human accountability.",
    ),
    Slide(
        30,
        "VERSIONED AGENT FLEET",
        "Discoverable agents with bounded authority",
        "Registry 0.2.0-r07 · three required agents · explicit tool, data, action, and prohibition scopes",
        (
            "governing_agent  → validate · route · block · pause · resume",
            "engineering_specialist  → calculate_network only",
            "verification_specialist  → independently_verify · canonical_sha256",
            "Prohibited: shell, arbitrary files, secrets, self-approval",
        ),
        GREEN,
        "terminal",
        "The registry makes every agent discoverable and versioned. Each role has explicit tools, data scope, authority, and prohibited actions. The deployed qualification found all three intended agents and all bounded tools.",
    ),
    Slide(
        35,
        "ACTUAL GOVERNED RESULT",
        "Deterministic calculation, independent verification",
        "Synthetic UTL-NET-001 · same qualified source tree used by the deployed successor",
        (
            "USER GOAL  →  GOVERNING AGENT  →  IEW SPECIALIST",
            "Darcy–Weisbach + Swamee–Jain  →  deterministic result",
            "Haaland recomputation  →  agreement within 5%  →  PASS",
            "HX-101  383.295650909 kPa   ·   HX-102  396.155258360 kPa",
            "STATE  AWAITING_HUMAN_REVIEW  ·  release_performed = false",
        ),
        BLUE,
        "result",
        "The primary method is Darcy–Weisbach with Swamee–Jain. The independent verifier uses Haaland and requires every segment to agree within five percent. Both endpoint residual pressures pass, and release remains blocked until review.",
    ),
    Slide(
        25,
        "PERSISTENCE + ASYNC",
        "Resume the same workflow in a fresh process",
        "Application-level persistent state is proven locally; Cloud Run cross-instance database durability is not claimed.",
        (
            "WFX-FBA87F708A47  ·  PAUSED at verification",
            "fresh process  ·  same workflow ID  ·  resumes to human review",
            "bounded worker  ·  no duplicate workflow on second pass",
            "10 timestamped events  ·  SQLite integrity: ok",
        ),
        PURPLE,
        "timeline",
        "The same workflow identity pauses after engineering, reopens in a fresh process, resumes at verification, and still cannot release itself. A bounded worker processes queued work without duplication.",
    ),
    Slide(
        25,
        "FORTIFIED CONTROLS",
        "Security, provenance, and human accountability",
        "Only neutral synthetic data is used. Operational traces record actions and outcomes, never hidden chain-of-thought.",
        (
            "Missing input  →  BLOCKED",
            "Prompt/tool injection  →  BLOCKED at workflow and tool boundaries",
            "Unallowlisted context  →  DO NOT USE",
            "Input · calculation · verification · registry hashes  →  MATCH",
            "Release  →  attributable reviewer required",
        ),
        GREEN,
        "controls",
        "Missing parameters are blocked instead of guessed. Injected instructions and unallowlisted context are rejected. Provenance hashes match, and an attributable reviewer remains required before release.",
    ),
    Slide(
        18,
        "CLOUD PROOF",
        "The affected live checks passed",
        "Authentic public-safe summary of the readback-verified private Cloud evidence archive",
        (
            "adk_agents_present  true     adk_tools_present  true",
            "adk_http_200  true           adk_model  true",
            "backend  VERTEX_AI           credential  ADC",
            "api_key_env_absent  true     logs_present  true",
            "SECRET_VALUES_LOGGED  false",
            "ARCHIVE SHA-256  7610a5a6…232be64a0c20b",
        ),
        GREEN,
        "terminal",
        "The active revision returned HTTP 200. The required agents, model, pass state, and bounded tools were present. Vertex AI, project, location, service identity, and logs were verified, with no API-key environment and no secret values logged.",
    ),
    Slide(
        12,
        "REPRODUCIBLE + JUDGE-ACCESSIBLE",
        "One public repository, explicit provenance",
        "Runtime source remains mapped even when later submission commits change documentation only.",
        (
            "github.com/moatazfarea/wexspace-iew-agentic-fleet",
            "deployed commit  da70a9b7bb08280f9c5d3c450e2171f28dea6c96",
            "deployed tree    6c572860fa041efde6b8bad8a19ed05d54465582",
            "README · architecture · tests · evidence · disclosures",
        ),
        BLUE,
        "repository",
        "The public repository includes reproducible setup, the architecture, tests, disclosures, and claim-to-evidence mappings. The deployed runtime commit and tree remain explicit even after documentation-only submission updates.",
    ),
    Slide(
        5,
        "WEXSPACE AI",
        "Bounded. Reproducible. Independently verified. Human-accountable.",
        "IEW is the first deeply qualified professional domain in the broader WEXSPACE architecture.",
        ("FINAL SUBMIT HAS NOT BEEN PERFORMED",),
        GREEN,
        "final",
        "WEXSPACE AI makes engineering agents useful by making them bounded, reproducible, independently verifiable, and human-accountable.",
    ),
)


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REGULAR)
    return ImageFont.truetype(str(path), size=size)


def rounded(draw: ImageDraw.ImageDraw, xy, fill, outline=None, radius=24, width=3):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def fit_lines(text: str, width: int, size: int, mono: bool = False) -> list[str]:
    approx = max(10, int(width / (size * (0.62 if mono else 0.54))))
    return textwrap.wrap(text, width=approx, break_long_words=False, break_on_hyphens=False) or [""]


def centered(draw, text, y, fnt, fill=INK):
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((WIDTH - (box[2] - box[0])) / 2, y), text, font=fnt, fill=fill)


def header(img: Image.Image, slide: Slide, number: int):
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 18), fill=slide.accent)
    draw.text((90, 62), slide.kicker, font=font(28, bold=True), fill=slide.accent)
    draw.text((90, 112), slide.title, font=font(55, bold=True), fill=NAVY)
    y = 190
    for line in fit_lines(slide.subtitle, 1740, 27):
        draw.text((92, y), line, font=font(27), fill=MUTED)
        y += 38
    draw.text((1745, 68), f"{number:02d}", font=font(24, bold=True), fill=MUTED)
    draw.text((90, 1025), "WEXSPACE AI — IEW Agentic Engineering Fleet", font=font(20, bold=True), fill=MUTED)
    draw.text((1500, 1025), "English on-screen narration", font=font(18), fill=MUTED)


def render_slide(slide: Slide, index: int) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), PALE)
    header(img, slide, index)
    draw = ImageDraw.Draw(img)
    top = 280

    if slide.layout == "architecture":
        art = Image.open(ARCHITECTURE).convert("RGB")
        art.thumbnail((1650, 700), Image.Resampling.LANCZOS)
        x = (WIDTH - art.width) // 2
        y = 286 + (700 - art.height) // 2
        rounded(draw, (x - 18, y - 18, x + art.width + 18, y + art.height + 18), WHITE, "#D8DFF1", 18, 2)
        img.paste(art, (x, y))
        return img

    if slide.layout == "hero":
        rounded(draw, (90, 290, 1830, 920), WHITE, slide.accent, 34, 4)
        draw.text((150, 338), "DEPLOYED + INVOKED", font=font(33, bold=True), fill=GREEN)
        y = 425
        for i, line in enumerate(slide.body):
            fnt = font(40 if i < 3 else 47, bold=i == 3, mono=i < 3)
            draw.text((150, y), line, font=fnt, fill=INK if i < 3 else GREEN)
            y += 105
        return img

    if slide.layout in {"terminal", "result", "repository"}:
        rounded(draw, (90, top, 1830, 920), NAVY, "#26385F", 28, 3)
        draw.ellipse((135, 322, 153, 340), fill="#FF5F57")
        draw.ellipse((168, 322, 186, 340), fill="#FEBC2E")
        draw.ellipse((201, 322, 219, 340), fill="#28C840")
        y = 395
        for i, line in enumerate(slide.body):
            for wrapped in fit_lines(line, 1570, 28, mono=True):
                draw.text((145, y), wrapped, font=font(28, mono=True), fill="#E8F0FF" if i < len(slide.body) - 1 else "#7FF0BD")
                y += 54
            y += 14
        return img

    if slide.layout == "timeline":
        x = 180
        y = 380
        colors = (BLUE, PURPLE, GREEN, AMBER)
        for i, line in enumerate(slide.body):
            draw.ellipse((x, y, x + 44, y + 44), fill=colors[i % len(colors)])
            if i < len(slide.body) - 1:
                draw.line((x + 22, y + 44, x + 22, y + 125), fill="#AAB7D6", width=5)
            draw.text((x + 90, y - 2), line, font=font(30, bold=i in {0, 1}), fill=INK)
            y += 135
        return img

    if slide.layout == "flow":
        y = 315
        for i, line in enumerate(slide.body):
            rounded(draw, (250, y, 1670, y + 115), WHITE, slide.accent, 24, 3)
            centered(draw, line, y + 34, font(29, bold=True), INK)
            if i < len(slide.body) - 1:
                draw.polygon(((945, y + 115), (975, y + 115), (960, y + 155)), fill=slide.accent)
            y += 155
        return img

    if slide.layout == "final":
        centered(draw, "7 / 7  TECHNICAL VICTORY", 335, font(52, bold=True), GREEN)
        centered(draw, "Google ADK  ·  Vertex AI  ·  Gemini 3.7 Flash  ·  Cloud Run", 440, font(31, bold=True), INK)
        centered(draw, slide.body[0], 620, font(30, bold=True), AMBER)
        return img

    cols = 2
    card_w, card_h = 800, 245
    for i, line in enumerate(slide.body):
        row, col = divmod(i, cols)
        x = 100 + col * 860
        y = 305 + row * 285
        rounded(draw, (x, y, x + card_w, y + card_h), WHITE, slide.accent, 26, 3)
        wrapped = fit_lines(line, card_w - 90, 31)
        text_y = y + (card_h - len(wrapped) * 43) / 2
        for part in wrapped:
            draw.text((x + 45, text_y), part, font=font(31, bold=True), fill=INK)
            text_y += 43
    return img


def srt_time(seconds: int) -> str:
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},000"


def write_subtitles() -> None:
    cursor = 0
    blocks = []
    for idx, slide in enumerate(SLIDES, 1):
        blocks.append(f"{idx}\n{srt_time(cursor)} --> {srt_time(cursor + slide.duration)}\n{slide.narration}\n")
        cursor += slide.duration
    SUBTITLES.write_text("\n".join(blocks), encoding="utf-8")


def render_video() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required")
    write_subtitles()
    with tempfile.TemporaryDirectory(prefix="wexspace-video-") as raw:
        tmp = Path(raw)
        segments = []
        for idx, slide in enumerate(SLIDES, 1):
            frame = render_slide(slide, idx)
            frame_path = tmp / f"slide-{idx:02d}.png"
            frame.save(frame_path, optimize=True)
            if idx == 1:
                frame.save(THUMBNAIL, optimize=True)
            segment = tmp / f"segment-{idx:02d}.mp4"
            fade_out = max(0, slide.duration - 0.35)
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-loop", "1", "-framerate", "30", "-i", str(frame_path),
                    "-t", str(slide.duration),
                    "-vf", f"fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out}:d=0.35,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "27",
                    "-r", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    str(segment),
                ],
                check=True,
            )
            segments.append(segment)
        concat_file = tmp / "concat.txt"
        concat_file.write_text("".join(f"file '{p}'\n" for p in segments), encoding="utf-8")
        video_only = tmp / "video-only.mp4"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-c", "copy", "-movflags", "+faststart", str(video_only),
            ],
            check=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(video_only), "-i", str(SUBTITLES),
                "-map", "0:v:0", "-map", "1:0", "-c:v", "copy", "-c:s", "mov_text",
                "-metadata:s:s:0", "language=eng", "-movflags", "+faststart", str(OUTPUT),
            ],
            check=True,
        )


if __name__ == "__main__":
    render_video()
    print(OUTPUT)
