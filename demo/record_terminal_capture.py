#!/usr/bin/env python3
"""Record authentic demo-run stdout as a continuous terminal video."""

from __future__ import annotations

import argparse
import os
import queue
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
RUNTIME = ROOT / "evidence" / "runtime" / "r02_live_capture"
PUBLIC_EVIDENCE = ROOT / "evidence" / "demo"
WIDTH, HEIGHT = 1920, 1080
FPS = 12
NAVY = "#071426"
PANEL = "#0D203A"
WHITE = "#F2F7FF"
MUTED = "#90A7C5"
GREEN = "#72E1A9"
BLUE = "#72B7FF"
AMBER = "#FFD279"
PURPLE = "#C7A9FF"
RED = "#FF8888"
FONT_ROOT = Path("/usr/share/fonts/truetype/dejavu")
FONT_MONO = FONT_ROOT / "DejaVuSansMono.ttf"
FONT_MONO_BOLD = FONT_ROOT / "DejaVuSansMono-Bold.ttf"
FONT_BOLD = FONT_ROOT / "DejaVuSans-Bold.ttf"


def font(size: int, *, bold: bool = False, mono: bool = True) -> ImageFont.FreeTypeFont:
    path = FONT_MONO_BOLD if mono and bold else FONT_MONO if mono else FONT_BOLD
    return ImageFont.truetype(str(path), size=size)


def color_for(line: str) -> str:
    if any(tag in line for tag in ("[FINAL VERIFIED RESULT]", "[CLOUD GATE]", "[RESULT]")):
        return GREEN
    if any(tag in line for tag in ("[AGENT]", "[ROUTE]", "[PUBLIC REPOSITORY]")):
        return BLUE
    if any(tag in line for tag in ("[TOOL]", "[ENGINEERING OUTPUT]", "[LIVE INVOCATION]")):
        return AMBER
    if any(tag in line for tag in ("[VERIFY]", "[INDEPENDENT METHOD]", "[VERTEX ASSERTIONS]")):
        return PURPLE
    if any(tag in line for tag in ("[STATE]", "[HUMAN GATE]", "ACCOUNTABLE HUMAN")):
        return RED
    if line.startswith("$"):
        return MUTED
    return WHITE


def wrap_output(line: str) -> list[str]:
    if not line:
        return [""]
    return textwrap.wrap(
        line,
        width=96,
        subsequent_indent="    ",
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]


def render(lines: list[str], title: str, subtitle: str, elapsed: float) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 16), fill=GREEN)
    draw.text((72, 45), title, font=font(35, bold=True, mono=False), fill=WHITE)
    draw.text((72, 98), subtitle, font=font(23, mono=False), fill=MUTED)
    timer = f"LIVE  {int(elapsed)//60:02d}:{int(elapsed)%60:02d}"
    draw.text((1650, 58), timer, font=font(25, bold=True), fill=GREEN)
    draw.rounded_rectangle((58, 155, 1862, 985), radius=22, fill=PANEL, outline="#29496E", width=3)
    draw.ellipse((91, 185, 109, 203), fill="#FF5F57")
    draw.ellipse((123, 185, 141, 203), fill="#FEBC2E")
    draw.ellipse((155, 185, 173, 203), fill="#28C840")
    display = lines[-19:]
    y = 235
    for line in display:
        draw.text((98, y), line, font=font(28), fill=color_for(line))
        y += 38
    draw.text(
        (72, 1015),
        "Authentic application stdout · continuous capture · no cuts · neutral synthetic data",
        font=font(20, mono=False),
        fill=MUTED,
    )
    return image


def runner_command(mode: str) -> tuple[list[str], str, str]:
    if mode == "live":
        RUNTIME.mkdir(parents=True, exist_ok=True)
        return (
            [sys.executable, str(DEMO / "live_demo_runner.py"), "--output-dir", str(RUNTIME)],
            "WEXSPACE AI — LIVE ENGINEERING WORKFLOW",
            "Continuous live run — actual AgentFleet events committed to persistent state",
        )
    return (
        [sys.executable, str(DEMO / "proof_demo_runner.py")],
        "WEXSPACE AI — REAL CLOUD + REPOSITORY PROOF",
        "Readback-verified Cloud execution record and deployed-source provenance",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("live", "proof"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--transcript", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    transcript = Path(args.transcript).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    transcript.parent.mkdir(parents=True, exist_ok=True)

    command, title, subtitle = runner_command(args.mode)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    if args.mode == "live":
        environment["WEXSPACE_DEMO_PACE"] = "1.15"
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    messages: queue.Queue[str | None] = queue.Queue()

    def read_output() -> None:
        assert process.stdout is not None
        for raw in process.stdout:
            messages.put(raw.rstrip("\n"))
        messages.put(None)

    threading.Thread(target=read_output, daemon=True).start()
    ffmpeg = subprocess.Popen(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
            "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "24", "-r", "30", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(output),
        ],
        stdin=subprocess.PIPE,
    )
    assert ffmpeg.stdin is not None
    visible: list[str] = []
    raw_lines: list[str] = []
    complete = False
    started = time.monotonic()
    next_frame = started
    while not complete:
        while True:
            try:
                item = messages.get_nowait()
            except queue.Empty:
                break
            if item is None:
                complete = True
                break
            raw_lines.append(item)
            visible.extend(wrap_output(item))
        now = time.monotonic()
        if now >= next_frame:
            frame = render(visible, title, subtitle, now - started)
            ffmpeg.stdin.write(frame.tobytes())
            next_frame += 1 / FPS
        else:
            time.sleep(min(0.02, next_frame - now))
    process.wait()
    hold_until = time.monotonic() + 2.5
    while time.monotonic() < hold_until:
        now = time.monotonic()
        frame = render(visible, title, subtitle, now - started)
        ffmpeg.stdin.write(frame.tobytes())
        time.sleep(1 / FPS)
    ffmpeg.stdin.close()
    if ffmpeg.wait() != 0 or process.returncode != 0:
        raise SystemExit(f"capture failed: runner={process.returncode} ffmpeg={ffmpeg.returncode}")
    transcript.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")

    if args.mode == "live":
        PUBLIC_EVIDENCE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            RUNTIME / "WEXSPACE_LIVE_RUN_R02.json",
            PUBLIC_EVIDENCE / "R07_VIDEO_R02_LIVE_RUN_RESULT.json",
        )
        shutil.copy2(
            RUNTIME / "live_trace.jsonl",
            PUBLIC_EVIDENCE / "R07_VIDEO_R02_LIVE_RUN_TRACE.jsonl",
        )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
