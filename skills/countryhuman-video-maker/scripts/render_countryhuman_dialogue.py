#!/usr/bin/env python3
"""Render a local CH-style voiced dialogue video from dialogue.json."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Optional


WIDTH = 1920
HEIGHT = 1080
FPS = 30

DEFAULT_COLORS = {
    "rabbit": "#d9242e",
    "camel": "#198754",
    "eagle": "#2563eb",
}

DEFAULT_VOICES = {
    "rabbit": "Bowen",
    "camel": "Anchen",
    "eagle": "Xinran",
}

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_VOICE_TTS_SCRIPT = SCRIPT_DIR.parent.parent / "voice-tts" / "scripts" / "tts.py"
DEFAULT_VIBEVOICE_ENV_FILE = Path.home() / ".cache/nick-skills/vibevoice/env.sh"


def run(command: list[str], *, quiet: bool = False, env: Optional[dict[str, str]] = None) -> subprocess.CompletedProcess[str]:
    stdout = subprocess.DEVNULL if quiet else None
    stderr = subprocess.DEVNULL if quiet else None
    try:
        return subprocess.run(command, check=True, text=True, stdout=stdout, stderr=stderr, env=env)
    except subprocess.CalledProcessError:
        raise


def require_binary(name: str) -> None:
    if not shutil.which(name):
        raise SystemExit(f"Required binary not found: {name}")


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return float(result.stdout.strip())


def ffprobe_streams(path: Path) -> list[str]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "csv=p=0",
            str(path),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "countryhuman-video"


def today_yyyymmdd() -> str:
    return datetime.now().strftime("%Y%m%d")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not data.get("title"):
        raise SystemExit("dialogue.json requires title")
    if not data.get("dialogue"):
        raise SystemExit("dialogue.json requires dialogue[]")
    return data


def parse_env_file(path: Path) -> dict[str, str]:
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("export "):
            continue
        for token in shlex.split(line[len("export ") :]):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            values[key] = value
    return values


def normalize_characters(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    characters = {}
    for raw in data.get("characters", []):
        char = dict(raw)
        char_id = char.get("id")
        if not char_id:
            raise SystemExit("Each character requires id")
        char.setdefault("name", char_id)
        char.setdefault("role", "")
        char.setdefault("voice", DEFAULT_VOICES.get(char_id, "Tingting"))
        char.setdefault("color", DEFAULT_COLORS.get(char_id, "#334155"))
        characters[char_id] = char
    for char_id in ("rabbit", "camel", "eagle"):
        characters.setdefault(
            char_id,
            {
                "id": char_id,
                "name": {"rabbit": "兔子", "camel": "骆驼", "eagle": "鹰酱"}[char_id],
                "role": {"rabbit": "中国", "camel": "沙特", "eagle": "美国"}[char_id],
                "voice": DEFAULT_VOICES[char_id],
                "color": DEFAULT_COLORS[char_id],
            },
        )
    return characters


def normalize_tasks(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = {}
    for index, raw in enumerate(data.get("tasks", []), start=1):
        task = dict(raw)
        task_id = task.get("id") or f"act-{index}"
        task["id"] = task_id
        task.setdefault("title", f"第{index}幕")
        task.setdefault("objective", "")
        task.setdefault("fact", "")
        tasks[task_id] = task
    if not tasks:
        tasks["act-1"] = {"id": "act-1", "title": "第一幕", "objective": "", "fact": ""}
    return tasks


def available_say_voices() -> set[str]:
    try:
        result = subprocess.run(["say", "-v", "?"], check=True, text=True, stdout=subprocess.PIPE)
    except Exception:
        return set()
    voices = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if parts:
            voices.add(parts[0])
    return voices


def pick_voice(requested: str, installed: set[str]) -> str:
    if requested in installed:
        return requested
    for fallback in ("Tingting", "Meijia", "Sinji"):
        if fallback in installed:
            return fallback
    if installed:
        return sorted(installed)[0]
    return requested


def wrap_text(text: str, max_units: float) -> list[str]:
    lines: list[str] = []
    current = ""
    units = 0.0
    for char in text:
        if char == "\n":
            if current:
                lines.append(current)
            current = ""
            units = 0.0
            continue
        width = 0.55 if ord(char) < 128 else 1.0
        if current and units + width > max_units:
            lines.append(current)
            current = char
            units = width
        else:
            current += char
            units += width
    if current:
        lines.append(current)
    return lines or [""]


def tspans(
    lines: list[str],
    x: int,
    y: int,
    size: int,
    *,
    fill: str = "#111827",
    weight: str = "500",
    anchor: str = "start",
) -> str:
    rendered = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else int(size * 1.28)
        rendered.append(f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>')
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" '
        'font-family="PingFang SC, Hiragino Sans GB, STHeiti, Arial Unicode MS, sans-serif">'
        + "".join(rendered)
        + "</text>"
    )


def star_points(cx: float, cy: float, outer: float, inner: float, count: int = 5, rotation: float = -90) -> str:
    points = []
    for index in range(count * 2):
        angle = math.radians(rotation + index * 180 / count)
        radius = outer if index % 2 == 0 else inner
        points.append(f"{cx + math.cos(angle) * radius:.1f},{cy + math.sin(angle) * radius:.1f}")
    return " ".join(points)


def rounded_rect(x: int, y: int, w: int, h: int, r: int, fill: str, stroke: str = "none", sw: int = 0, opacity: float = 1.0) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>'
    )


def character_svg(char: dict[str, Any], x: int, y: int, active: bool) -> str:
    char_id = char.get("id")
    opacity = 1.0 if active else 0.56
    color = char.get("color", "#334155")
    glow = ""
    if active:
        glow = (
            f'<ellipse cx="{x}" cy="{y+20}" rx="148" ry="178" fill="{color}" opacity="0.13"/>'
            f'<ellipse cx="{x}" cy="{y+20}" rx="132" ry="162" fill="none" stroke="{color}" stroke-width="9" opacity="0.85"/>'
        )

    body = ch_body_svg(char_id, x, y, color, opacity)

    if char_id == "rabbit":
        head = rabbit_head(x, y, opacity)
    elif char_id == "camel":
        head = camel_head(x, y, opacity)
    elif char_id == "eagle":
        head = eagle_head(x, y, opacity)
    else:
        head = generic_head(x, y, color, opacity)

    name = escape(f"{char.get('name', char_id)} / {char.get('role', '')}".strip(" /"))
    label = (
        f'<rect x="{x-134}" y="{y+238}" width="268" height="52" rx="8" fill="#111827" opacity="{0.92 if active else 0.45}"/>'
        f'<text x="{x}" y="{y+272}" text-anchor="middle" font-size="28" fill="#ffffff" font-weight="700" '
        'font-family="PingFang SC, Hiragino Sans GB, STHeiti, Arial Unicode MS, sans-serif">'
        f"{name}</text>"
    )
    return f"{body}{glow}{head}{label}"


def ch_body_svg(char_id: str, x: int, y: int, color: str, opacity: float) -> str:
    jacket = {"rabbit": "#1f2937", "camel": "#f8fafc", "eagle": "#111827"}.get(char_id, "#1f2937")
    shirt = {"rabbit": "#d9242e", "camel": "#198754", "eagle": "#f8fafc"}.get(char_id, color)
    tie = {"rabbit": "#f8fafc", "camel": "#d8b45b", "eagle": "#c91f37"}.get(char_id, "#f8fafc")
    scarf = ""
    if char_id == "camel":
        scarf = (
            f'<path d="M{x-70},{y+122} C{x-22},{y+154} {x+22},{y+154} {x+70},{y+122} '
            f'L{x+48},{y+186} C{x+18},{y+174} {x-18},{y+174} {x-48},{y+186}Z" fill="#d8b45b" opacity="0.96"/>'
        )
    return f"""
    <g opacity="{opacity}">
      <path d="M{x-46},{y+86} C{x-32},{y+118} {x+32},{y+118} {x+46},{y+86} L{x+54},{y+146} C{x+20},{y+168} {x-20},{y+168} {x-54},{y+146}Z" fill="#e5e7eb"/>
      <path d="M{x-142},{y+138} C{x-180},{y+218} {x+180},{y+218} {x+142},{y+138} C{x+88},{y+104} {x-88},{y+104} {x-142},{y+138}Z" fill="{jacket}"/>
      <path d="M{x-64},{y+132} L{x},{y+218} L{x+64},{y+132} C{x+28},{y+150} {x-28},{y+150} {x-64},{y+132}Z" fill="{shirt}" opacity="0.95"/>
      <path d="M{x-20},{y+136} L{x},{y+168} L{x+20},{y+136} L{x+10},{y+206} L{x-10},{y+206}Z" fill="{tie}" opacity="0.95"/>
      <path d="M{x-138},{y+160} C{x-92},{y+142} {x-62},{y+138} {x-28},{y+156}" fill="none" stroke="#ffffff" stroke-width="8" opacity="0.18"/>
      <path d="M{x+138},{y+160} C{x+92},{y+142} {x+62},{y+138} {x+28},{y+156}" fill="none" stroke="#ffffff" stroke-width="8" opacity="0.18"/>
      {scarf}
    </g>
    """


def face_path(x: int, y: int) -> str:
    return (
        f"M{x-96},{y-76} C{x-64},{y-118} {x+64},{y-118} {x+96},{y-76} "
        f"L{x+92},{y+62} C{x+54},{y+106} {x-54},{y+106} {x-92},{y+62}Z"
    )


def hair_svg(x: int, y: int, opacity: float, accent: str = "#f8fafc") -> str:
    return f"""
    <g opacity="{opacity}">
      <path d="M{x-112},{y-58} C{x-108},{y-142} {x-38},{y-184} {x+34},{y-166} C{x+94},{y-150} {x+124},{y-96} {x+112},{y-34} L{x+86},{y-88} L{x+58},{y-24} L{x+24},{y-98} L{x-8},{y-18} L{x-46},{y-96} L{x-72},{y-20}Z" fill="{accent}" stroke="#111827" stroke-width="5"/>
      <path d="M{x-118},{y-30} C{x-154},{y+20} {x-132},{y+96} {x-82},{y+128}" fill="none" stroke="{accent}" stroke-width="28" stroke-linecap="round"/>
      <path d="M{x+118},{y-30} C{x+154},{y+22} {x+128},{y+94} {x+84},{y+126}" fill="none" stroke="{accent}" stroke-width="28" stroke-linecap="round"/>
      <path d="M{x-50},{y-144} L{x-22},{y-52} L{x+8},{y-136} L{x+42},{y-56}" fill="none" stroke="#dbeafe" stroke-width="8" opacity="0.56"/>
    </g>
    """


def rabbit_head(x: int, y: int, opacity: float) -> str:
    clip = f"rabbitClip{x}"
    return f"""
    {hair_svg(x, y, opacity)}
    <defs><clipPath id="{clip}"><path d="{face_path(x, y)}"/></clipPath></defs>
    <g clip-path="url(#{clip})" opacity="{opacity}">
      <rect x="{x-104}" y="{y-116}" width="208" height="222" fill="#d9242e"/>
      <polygon points="{star_points(x-48, y-42, 32, 13)}" fill="#ffd23f"/>
      <polygon points="{star_points(x+4, y-76, 12, 5)}" fill="#ffd23f"/>
      <polygon points="{star_points(x+34, y-42, 12, 5)}" fill="#ffd23f"/>
      <polygon points="{star_points(x+34, y+8, 12, 5)}" fill="#ffd23f"/>
      <polygon points="{star_points(x+4, y+42, 12, 5)}" fill="#ffd23f"/>
    </g>
    <path d="{face_path(x, y)}" fill="none" stroke="#111827" stroke-width="6" opacity="{opacity}"/>
    <path d="M{x-42},{y+12} L{x-12},{y+12}" stroke="#111827" stroke-width="8" stroke-linecap="round" opacity="{opacity}"/>
    <path d="M{x+16},{y+12} L{x+46},{y+12}" stroke="#111827" stroke-width="8" stroke-linecap="round" opacity="{opacity}"/>
    <path d="M{x-34},{y+58} Q{x},{y+72} {x+34},{y+58}" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" opacity="{opacity}"/>
    """


def camel_head(x: int, y: int, opacity: float) -> str:
    clip = f"camelClip{x}"
    return f"""
    {hair_svg(x, y, opacity, "#f4f4f5")}
    <path d="M{x-104},{y-94} C{x-42},{y-142} {x+42},{y-142} {x+104},{y-94}" fill="none" stroke="#d8b45b" stroke-width="24" stroke-linecap="round" opacity="{opacity}"/>
    <defs><clipPath id="{clip}"><path d="{face_path(x, y)}"/></clipPath></defs>
    <g clip-path="url(#{clip})" opacity="{opacity}">
      <rect x="{x-104}" y="{y-116}" width="208" height="222" fill="#198754"/>
      <path d="M{x-64},{y-46} C{x-24},{y-70} {x+24},{y-70} {x+64},{y-46}" fill="none" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
      <path d="M{x-62},{y+48} L{x+76},{y+20}" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
      <path d="M{x+76},{y+20} L{x+48},{y+42}" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
    </g>
    <path d="{face_path(x, y)}" fill="none" stroke="#111827" stroke-width="6" opacity="{opacity}"/>
    <circle cx="{x-34}" cy="{y+4}" r="11" fill="#ffffff" opacity="{opacity}"/>
    <circle cx="{x+34}" cy="{y+4}" r="11" fill="#ffffff" opacity="{opacity}"/>
    <path d="M{x-36},{y+58} Q{x},{y+72} {x+36},{y+58}" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" opacity="{opacity}"/>
    """


def eagle_head(x: int, y: int, opacity: float) -> str:
    clip = f"eagleClip{x}"
    stripes = []
    for index in range(8):
        color = "#c91f37" if index % 2 == 0 else "#ffffff"
        stripes.append(f'<rect x="{x-104}" y="{y-116 + index * 28}" width="208" height="28" fill="{color}"/>')
    stars = []
    for row in range(3):
        for col in range(4):
            stars.append(f'<circle cx="{x-74 + col * 24}" cy="{y-84 + row * 24}" r="4.5" fill="#ffffff"/>')
    return f"""
    {hair_svg(x, y, opacity)}
    <defs><clipPath id="{clip}"><path d="{face_path(x, y)}"/></clipPath></defs>
    <g clip-path="url(#{clip})" opacity="{opacity}">
      {''.join(stripes)}
      <rect x="{x-104}" y="{y-116}" width="104" height="92" fill="#23408e"/>
      {''.join(stars)}
    </g>
    <path d="{face_path(x, y)}" fill="none" stroke="#111827" stroke-width="6" opacity="{opacity}"/>
    <rect x="{x-76}" y="{y-14}" width="62" height="36" rx="8" fill="#111827" opacity="{opacity}"/>
    <rect x="{x+14}" y="{y-14}" width="62" height="36" rx="8" fill="#111827" opacity="{opacity}"/>
    <line x1="{x-14}" y1="{y+4}" x2="{x+14}" y2="{y+4}" stroke="#111827" stroke-width="8" opacity="{opacity}"/>
    <path d="M{x-34},{y+68} Q{x+8},{y+86} {x+52},{y+68}" fill="none" stroke="#111827" stroke-width="8" stroke-linecap="round" opacity="{opacity}"/>
    """


def generic_head(x: int, y: int, color: str, opacity: float) -> str:
    return f"""
    {hair_svg(x, y, opacity)}
    <path d="{face_path(x, y)}" fill="{color}" stroke="#111827" stroke-width="6" opacity="{opacity}"/>
    <circle cx="{x-38}" cy="{y+4}" r="13" fill="#ffffff" opacity="{opacity}"/>
    <circle cx="{x+38}" cy="{y+4}" r="13" fill="#ffffff" opacity="{opacity}"/>
    <path d="M{x-36},{y+58} Q{x},{y+72} {x+36},{y+58}" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" opacity="{opacity}"/>
    """


def render_svg(
    data: dict[str, Any],
    characters: dict[str, dict[str, Any]],
    tasks: dict[str, dict[str, Any]],
    line: dict[str, Any],
    index: int,
    total: int,
    start_sec: float,
    duration_sec: float,
) -> str:
    speaker_id = line.get("speaker", "")
    task = tasks.get(line.get("task"), next(iter(tasks.values())))
    title = data.get("title", "国拟人对话视频")
    task_title = task.get("title", "")
    objective = task.get("objective", "")
    fact = line.get("fact") or task.get("fact") or ""
    speaker = characters.get(speaker_id, {"name": speaker_id, "role": "", "color": "#334155"})
    text = line.get("caption") or line.get("text", "")
    bubble_lines = wrap_text(text, 43)
    objective_lines = wrap_text(objective, 34)
    fact_lines = wrap_text(fact, 42)
    progress = (index + 1) / max(total, 1)
    progress_width = int(1320 * progress)
    active_color = speaker.get("color", "#334155")
    speaker_name = f"{speaker.get('name', speaker_id)}："
    x_positions = {"rabbit": 470, "camel": 960, "eagle": 1450}
    ordered_ids = ["rabbit", "camel", "eagle"]
    ordered_ids += [char_id for char_id in characters if char_id not in ordered_ids]
    fallback_positions = [360, 720, 1080, 1440]
    character_groups = []
    for pos_index, char_id in enumerate(ordered_ids[:4]):
        x = x_positions.get(char_id, fallback_positions[min(pos_index, len(fallback_positions) - 1)])
        character_groups.append(character_svg(characters[char_id], x, 500, char_id == speaker_id))

    style = data.get("style", "国拟人对话")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#f7fbf7"/>
  <path d="M0,0 H1920 V220 C1500,180 1180,250 900,210 C600,170 330,220 0,185 Z" fill="#e8f3ef"/>
  <path d="M0,900 C260,820 520,905 790,840 C1070,772 1320,870 1920,790 V1080 H0 Z" fill="#dceee5"/>
  <g opacity="0.22">
    <path d="M128,160 H1780" stroke="#2f855a" stroke-width="2"/>
    <path d="M170,250 H1750" stroke="#2f855a" stroke-width="2"/>
    <path d="M105,740 H1815" stroke="#2f855a" stroke-width="2"/>
    <circle cx="1700" cy="170" r="52" fill="#d9242e"/>
    <circle cx="182" cy="810" r="48" fill="#2563eb"/>
  </g>

  <text x="110" y="96" font-size="46" fill="#111827" font-weight="800"
    font-family="PingFang SC, Hiragino Sans GB, STHeiti, Arial Unicode MS, sans-serif">{escape(title)}</text>
  <text x="112" y="148" font-size="27" fill="#334155" font-weight="600"
    font-family="PingFang SC, Hiragino Sans GB, STHeiti, Arial Unicode MS, sans-serif">国拟人对话 · {escape(style)} · 第 {index + 1}/{total} 句 · {start_sec:.1f}秒 - {start_sec + duration_sec:.1f}秒</text>

  <rect x="300" y="184" width="1320" height="12" rx="6" fill="#cbd5e1"/>
  <rect x="300" y="184" width="{progress_width}" height="12" rx="6" fill="{active_color}"/>

  <ellipse cx="960" cy="724" rx="620" ry="104" fill="#a7c7b9" opacity="0.62"/>
  <rect x="392" y="655" width="1136" height="84" rx="8" fill="#48635b"/>
  <rect x="454" y="680" width="1012" height="38" rx="8" fill="#729486" opacity="0.9"/>

  {''.join(character_groups)}

  {rounded_rect(104, 190, 560, 112, 8, "#ffffff", "#cbd5e1", 3, 0.97)}
  <text x="136" y="236" font-size="32" fill="#111827" font-weight="800"
    font-family="PingFang SC, Hiragino Sans GB, STHeiti, Arial Unicode MS, sans-serif">{escape(task_title)}</text>
  {tspans(objective_lines[:1], 136, 276, 24, fill="#475569", weight="600")}

  {rounded_rect(1256, 190, 560, 112, 8, "#ffffff", "#cbd5e1", 3, 0.97)}
  <text x="1288" y="236" font-size="30" fill="#111827" font-weight="800"
    font-family="PingFang SC, Hiragino Sans GB, STHeiti, Arial Unicode MS, sans-serif">关键事实</text>
  {tspans(fact_lines[:1], 1288, 276, 23, fill="#475569", weight="600")}

  <g>
    {rounded_rect(174, 808, 1572, 190, 8, "#ffffff", "#111827", 4, 0.98)}
    <rect x="174" y="808" width="1572" height="18" rx="8" fill="{active_color}"/>
    <text x="226" y="872" font-size="38" fill="{active_color}" font-weight="900"
      font-family="PingFang SC, Hiragino Sans GB, STHeiti, Arial Unicode MS, sans-serif">{escape(speaker_name)}</text>
    {tspans(bubble_lines[:3], 226, 925, 39, fill="#111827", weight="800")}
  </g>
</svg>
"""


def convert_svg_to_png(svg_path: Path, png_path: Path) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    run(["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)], quiet=True)


def synthesize_say(text: str, voice: str, rate: int, raw_output: Path) -> None:
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    run(["say", "-v", voice, "-r", str(rate), "-o", str(raw_output), text], quiet=True)


def synthesize_voice_tts(
    text: str,
    speaker_id: str,
    output_wav: Path,
    args: argparse.Namespace,
    env: dict[str, str],
) -> None:
    tts_script = Path(args.voice_tts_script).expanduser().resolve()
    if not tts_script.exists():
        raise SystemExit(f"voice-tts script not found: {tts_script}")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as tmp:
        tmp.write(text)
        text_file = tmp.name
    try:
        command = [
            sys.executable,
            str(tts_script),
            "-f",
            text_file,
            "-o",
            str(output_wav),
            "--speaker-id",
            speaker_id,
            "--seed",
            str(args.vibevoice_seed),
            "--language",
            "zh",
            "--cfg-scale",
            str(args.vibevoice_cfg_scale),
            "--no-ensure",
        ]
        run(command, quiet=False if args.verbose_tts else True, env=env)
    finally:
        Path(text_file).unlink(missing_ok=True)


def normalize_audio(raw_audio: Path, output_wav: Path, duration_sec: float) -> None:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(raw_audio),
            "-af",
            "apad",
            "-t",
            f"{duration_sec:.3f}",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(output_wav),
        ],
        quiet=True,
    )


def render_segment(frame_png: Path, audio_wav: Path, duration_sec: float, segment_mp4: Path) -> None:
    segment_mp4.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(frame_png),
            "-i",
            str(audio_wav),
            "-t",
            f"{duration_sec:.3f}",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            str(segment_mp4),
        ],
        quiet=True,
    )


def concat_segments(segments: list[Path], output_mp4: Path) -> None:
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    concat_file = output_mp4.parent / "segments.txt"
    with concat_file.open("w", encoding="utf-8") as file:
        for segment in segments:
            safe_path = str(segment.resolve()).replace("'", "'\\''")
            file.write(f"file '{safe_path}'\n")
    try:
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output_mp4),
            ],
            quiet=True,
        )
    except subprocess.CalledProcessError:
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(FPS),
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                str(output_mp4),
            ],
            quiet=True,
        )


def write_markdown_files(base_dir: Path, data: dict[str, Any], characters: dict[str, dict[str, Any]], tasks: dict[str, dict[str, Any]]) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    title = data.get("title", "")
    character_summary = "、".join(f"{char.get('name')}({char.get('role')})" for char in characters.values())
    act_summary = " / ".join(task.get("title", "") for task in tasks.values())
    brief = [
        f"# {title}",
        "",
        f"- 风格：{data.get('style', '国拟人对话')}",
        f"- 目标时长：{data.get('targetDurationSec', 180)} 秒",
        f"- 角色：{character_summary}",
        f"- 故事结构：{act_summary}",
    ]
    (base_dir / "brief.md").write_text("\n".join(brief) + "\n", encoding="utf-8")

    script_lines = [f"# {title} - 对话脚本", ""]
    current_task = None
    for line in data["dialogue"]:
        task_id = line.get("task")
        if task_id != current_task:
            current_task = task_id
            task = tasks.get(task_id, {})
            script_lines.extend([f"## {task.get('title', task_id)}", "", f"{task.get('objective', '')}", ""])
        speaker = characters.get(line.get("speaker", ""), {"name": line.get("speaker", "")})
        script_lines.append(f"- **{speaker.get('name')}**：{line.get('text', '')}")
    (base_dir / "script.md").write_text("\n".join(script_lines) + "\n", encoding="utf-8")

    storyboard_lines = [f"# {title} - 分镜", ""]
    for index, line in enumerate(data["dialogue"], start=1):
        speaker = characters.get(line.get("speaker", ""), {"name": line.get("speaker", "")})
        task = tasks.get(line.get("task"), {})
        storyboard_lines.extend(
            [
                f"## 镜头 {index:02d}",
                "",
                f"- 段落：{task.get('title', '')}",
                f"- 说话者：{speaker.get('name', '')}",
                f"- 画面：三角色桌边构图，{speaker.get('name', '')} 高亮，底部气泡显示当前台词。",
                f"- 台词：{line.get('text', '')}",
                "",
            ]
        )
    (base_dir / "storyboard.md").write_text("\n".join(storyboard_lines), encoding="utf-8")

    source_lines = [f"# {title} - Sources", ""]
    sources = data.get("sources") or []
    if sources:
        for item in sources:
            if isinstance(item, str):
                source_lines.append(f"- {item}")
            else:
                source_lines.append(f"- [{item.get('title', item.get('url', 'source'))}]({item.get('url', '')})：{item.get('fact', '')}")
    else:
        source_lines.append("- 未提供外部来源。")
    (base_dir / "sources.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")


def write_summary(output_dir: Path, slug: str, data: dict[str, Any]) -> None:
    summary = data.get("summary", {})
    title = summary.get("title") or data.get("title", "")[:16]
    copy = summary.get("copy") or "一段冷战末期的地缘交易，三句话看懂需求、交易和后果。"
    hashtags = " ".join(summary.get("hashtags", []))
    backup = summary.get("backup")
    lines = [f"标题：{title}", "", f"发布文案：{copy}"]
    if hashtags:
        lines.extend(["", f"话题标签：{hashtags}"])
    if backup:
        lines.extend(["", f"备用短句：{backup}"])
    (output_dir / f"{slug}-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def planned_duration(line: dict[str, Any], default_duration: float) -> float:
    try:
        return float(line.get("durationSec", default_duration))
    except (TypeError, ValueError):
        return default_duration


def resolve_audio_file(value: str, input_path: Path, base_dir: Path) -> Path:
    audio_path = Path(value).expanduser()
    if audio_path.is_absolute():
        return audio_path
    for root in (input_path.parent, base_dir):
        candidate = root / audio_path
        if candidate.exists():
            return candidate
    return input_path.parent / audio_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a local CH-style dialogue video.")
    parser.add_argument("--input", required=True, help="Path to dialogue.json")
    parser.add_argument("--output-root", default="countryhuman-video", help="Output root directory")
    parser.add_argument("--slug", help="Override output slug")
    parser.add_argument("--date", default=today_yyyymmdd(), help="YYYYMMDD output date")
    parser.add_argument("--voice-engine", choices=["voice-tts", "say"], default="voice-tts", help="Local voice engine")
    parser.add_argument("--voice-tts-script", default=str(DEFAULT_VOICE_TTS_SCRIPT), help="Path to voice-tts/scripts/tts.py")
    parser.add_argument("--vibevoice-env-file", default=str(DEFAULT_VIBEVOICE_ENV_FILE), help="Path to local VibeVoice env.sh")
    parser.add_argument("--vibevoice-seed", default="1227", help="Stable VibeVoice seed")
    parser.add_argument("--vibevoice-cfg-scale", default="1.3", help="VibeVoice cfg scale")
    parser.add_argument("--verbose-tts", action="store_true", help="Show voice-tts model logs")
    parser.add_argument("--reuse-audio", action="store_true", help="Reuse existing generated audio files when present")
    parser.add_argument("--say-rate", type=int, default=178, help="macOS say speaking rate")
    parser.add_argument("--keep-svg", action="store_true", help="Keep intermediate SVG frames")
    args = parser.parse_args()

    for binary in ("ffmpeg", "ffprobe", "sips"):
        require_binary(binary)
    if args.voice_engine == "say":
        require_binary("say")

    input_path = Path(args.input).expanduser().resolve()
    data = load_json(input_path)
    characters = normalize_characters(data)
    tasks = normalize_tasks(data)
    slug = args.slug or data.get("slug") or slugify(data.get("title", "countryhuman-video"))
    base_dir = Path(args.output_root) / args.date / slug
    if input_path.name == "dialogue.json":
        base_dir = input_path.parent
    audio_dir = base_dir / "audio"
    frames_dir = base_dir / "frames"
    segments_dir = base_dir / "segments"
    output_dir = base_dir / "output"
    output_mp4 = output_dir / f"{slug}.mp4"
    base_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.resolve() != (base_dir / "dialogue.json").resolve():
        (base_dir / "dialogue.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    write_markdown_files(base_dir, data, characters, tasks)
    write_summary(output_dir, slug, data)

    installed_voices = available_say_voices() if args.voice_engine == "say" else set()
    voice_tts_env = os.environ.copy()
    if args.voice_engine == "voice-tts":
        env_file = Path(args.vibevoice_env_file).expanduser()
        voice_tts_env.update(parse_env_file(env_file))
        if not voice_tts_env.get("VIBEVOICE_TTS_CMD"):
            raise SystemExit(
                "Local VibeVoice is not configured. Run skills/voice-tts/scripts/ensure_vibevoice.sh first, "
                "or pass --voice-engine say for the lower-quality macOS fallback."
            )
    lines = data["dialogue"]
    default_line_duration = float(data.get("targetDurationSec", 180)) / max(len(lines), 1)
    timings = []
    segments: list[Path] = []
    current_start = 0.0

    for index, line in enumerate(lines):
        speaker_id = line.get("speaker")
        speaker = characters.get(speaker_id, {"voice": "Tingting", "name": speaker_id, "color": "#334155"})
        text = str(line.get("text", "")).strip()
        spoken_text = str(line.get("spokenText") or text).strip()
        if not text:
            raise SystemExit(f"dialogue[{index}] has empty text")

        planned = planned_duration(line, default_line_duration)
        raw_audio = audio_dir / f"line-{index + 1:02d}.aiff"
        wav_audio = audio_dir / f"line-{index + 1:02d}.wav"
        svg_frame = frames_dir / f"line-{index + 1:02d}.svg"
        png_frame = frames_dir / f"line-{index + 1:02d}.png"
        segment = segments_dir / f"line-{index + 1:02d}.mp4"
        external_audio = line.get("audioFile")

        if external_audio:
            source_audio = resolve_audio_file(str(external_audio), input_path, base_dir)
            if not source_audio.exists():
                raise SystemExit(f"dialogue[{index}] audioFile not found: {source_audio}")
            voice = "external"
            raw_duration = ffprobe_duration(source_audio)
            print(f"[{index + 1:02d}/{len(lines):02d}] {speaker.get('name', speaker_id)} -> 外部音频: {text[:36]}", flush=True)
            duration = max(planned, raw_duration + 0.35)
            normalize_audio(source_audio, wav_audio, duration)
        elif args.voice_engine == "voice-tts":
            requested_voice = str(line.get("voice") or speaker.get("voice") or "Bowen")
            raw_wav = audio_dir / f"line-{index + 1:02d}-vibevoice.wav"
            if args.reuse_audio and raw_wav.exists():
                print(f"[{index + 1:02d}/{len(lines):02d}] {speaker.get('name', speaker_id)} -> 复用 VibeVoice/{requested_voice}: {text[:36]}", flush=True)
            else:
                print(f"[{index + 1:02d}/{len(lines):02d}] {speaker.get('name', speaker_id)} -> VibeVoice/{requested_voice}: {text[:36]}", flush=True)
                synthesize_voice_tts(spoken_text, requested_voice, raw_wav, args, voice_tts_env)
            raw_duration = ffprobe_duration(raw_wav)
            duration = max(planned, raw_duration + 0.35)
            normalize_audio(raw_wav, wav_audio, duration)
            voice = requested_voice
        else:
            requested_voice = str(line.get("voice") or speaker.get("voice") or "Tingting")
            voice = pick_voice(requested_voice, installed_voices)
            print(f"[{index + 1:02d}/{len(lines):02d}] {speaker.get('name', speaker_id)} -> say/{voice}: {text[:36]}", flush=True)
            synthesize_say(spoken_text, voice, args.say_rate, raw_audio)
            raw_duration = ffprobe_duration(raw_audio)
            duration = max(planned, raw_duration + 0.35)
            normalize_audio(raw_audio, wav_audio, duration)

        svg = render_svg(data, characters, tasks, line, index, len(lines), current_start, duration)
        svg_frame.parent.mkdir(parents=True, exist_ok=True)
        svg_frame.write_text(svg, encoding="utf-8")
        convert_svg_to_png(svg_frame, png_frame)
        if not args.keep_svg:
            svg_frame.unlink(missing_ok=True)
        render_segment(png_frame, wav_audio, duration, segment)

        timings.append(
            {
                "id": f"line-{index + 1:02d}",
                "task": line.get("task"),
                "speaker": speaker_id,
                "voice": voice,
                "startSec": round(current_start, 3),
                "durationSec": round(duration, 3),
                "audioFile": str(wav_audio.relative_to(base_dir)),
                "frameFile": str(png_frame.relative_to(base_dir)),
                "text": text,
            }
        )
        current_start += duration
        segments.append(segment)

    concat_segments(segments, output_mp4)
    actual_duration = ffprobe_duration(output_mp4)
    streams = ffprobe_streams(output_mp4)
    timing = {
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "style": data.get("style", "国拟人对话"),
        "targetDurationSec": data.get("targetDurationSec", 180),
        "actualDurationSec": round(actual_duration, 3),
        "voiceEngine": args.voice_engine,
        "vibevoiceSeed": args.vibevoice_seed if args.voice_engine == "voice-tts" else None,
        "vibevoiceCfgScale": args.vibevoice_cfg_scale if args.voice_engine == "voice-tts" else None,
        "sayRate": args.say_rate,
        "streams": streams,
        "lines": timings,
    }
    (base_dir / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if "video" not in streams or "audio" not in streams:
        raise SystemExit(f"Rendered file is missing expected streams: {streams}")

    print("")
    print(f"Rendered: {output_mp4}")
    print(f"Duration: {actual_duration:.2f}s")
    print(f"Streams: {', '.join(streams)}")


if __name__ == "__main__":
    main()
