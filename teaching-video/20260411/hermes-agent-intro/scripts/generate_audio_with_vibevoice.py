#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NARRATION = ROOT / "narration.md"
AUDIO_DIR = ROOT / "audio"
DRAFT_TIMING = ROOT / "timing.draft.json"
TIMING = ROOT / "timing.json"
REMOTION_TIMING = ROOT / "remotion" / "src" / "timing.generated.ts"


def read_scenes():
    text = NARRATION.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^## (Scene \d+) - (.+)$", text, flags=re.M))
    scenes = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        scene_id = f"scene-{index + 1:02d}"
        scenes.append(
            {
                "id": scene_id,
                "title": match.group(2).strip(),
                "text": text[start:end].strip(),
                "audio": AUDIO_DIR / f"{scene_id}.wav",
            }
        )
    return scenes


def render_http(scene):
    endpoint = os.environ["VIBEVOICE_ENDPOINT"].rstrip("/")
    payload = {
        "model": os.environ.get("VIBEVOICE_MODEL", "microsoft/VibeVoice-1.5B"),
        "text": scene["text"],
        "language": os.environ.get("VIBEVOICE_LANGUAGE", "zh"),
        "speaker_id": os.environ.get("VIBEVOICE_SPEAKER_ID", ""),
        "voice_reference": os.environ.get("VIBEVOICE_VOICE_REF", ""),
        "output_path": str(scene["audio"]),
        "format": os.environ.get("VIBEVOICE_AUDIO_FORMAT", "wav"),
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = resp.read()
        ctype = resp.headers.get("Content-Type", "")
    if ctype.startswith("audio/"):
        scene["audio"].write_bytes(body)
        return
    try:
        result = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise RuntimeError(f"Unexpected VibeVoice HTTP response for {scene['id']}: {body[:200]!r}")
    returned_path = result.get("output_path") or result.get("path") or result.get("file")
    if returned_path and Path(returned_path).exists() and Path(returned_path) != scene["audio"]:
        scene["audio"].write_bytes(Path(returned_path).read_bytes())
    if not scene["audio"].exists():
        raise RuntimeError(f"VibeVoice did not create {scene['audio']}")


def render_command(scene):
    template = os.environ["VIBEVOICE_TTS_CMD"]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as tmp:
        tmp.write(scene["text"])
        text_file = tmp.name
    values = {
        "model": os.environ.get("VIBEVOICE_MODEL", "microsoft/VibeVoice-1.5B"),
        "text": scene["text"],
        "text_file": text_file,
        "output": str(scene["audio"]),
        "voice_ref": os.environ.get("VIBEVOICE_VOICE_REF", ""),
        "speaker_id": os.environ.get("VIBEVOICE_SPEAKER_ID", ""),
        "language": os.environ.get("VIBEVOICE_LANGUAGE", "zh"),
    }
    command = template.format(**{key: shlex.quote(value) for key, value in values.items()})
    subprocess.run(command, shell=True, check=True)
    Path(text_file).unlink(missing_ok=True)
    if not scene["audio"].exists():
        raise RuntimeError(f"VibeVoice command did not create {scene['audio']}")


def duration(path):
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
        capture_output=True,
    )
    return round(float(result.stdout.strip()), 3)


def main():
    if not os.environ.get("VIBEVOICE_ENDPOINT") and not os.environ.get("VIBEVOICE_TTS_CMD"):
        raise SystemExit("Set VIBEVOICE_ENDPOINT or VIBEVOICE_TTS_CMD before generating audio.")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    scenes = read_scenes()
    for scene in scenes:
        print(f"Generating {scene['id']}: {scene['title']}")
        if os.environ.get("VIBEVOICE_ENDPOINT"):
            try:
                render_http(scene)
            except urllib.error.URLError as exc:
                raise RuntimeError(f"VibeVoice endpoint failed for {scene['id']}: {exc}") from exc
        else:
            render_command(scene)

    draft = json.loads(DRAFT_TIMING.read_text(encoding="utf-8"))
    start = 0.0
    actual_scenes = []
    for draft_scene, scene in zip(draft["scenes"], scenes):
        sec = duration(scene["audio"])
        actual_scenes.append(
            {
                **draft_scene,
                "startSec": round(start, 3),
                "durationSec": sec,
                "audioFile": f"../audio/{scene['audio'].name}",
                "narration": scene["text"],
            }
        )
        start += sec
    draft["status"] = "measured_from_vibevoice_audio"
    draft["actualDurationSec"] = round(start, 3)
    draft["scenes"] = actual_scenes
    TIMING.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    remotion_scenes = [
        {
            "id": scene["id"],
            "title": scene["title"],
            "durationSec": scene["durationSec"],
            "audioFile": scene["audioFile"],
            "asset": scene["asset"],
            "hasAudio": True,
        }
        for scene in actual_scenes
    ]
    REMOTION_TIMING.write_text(
        "export const scenes = "
        + json.dumps(remotion_scenes, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {TIMING}")
    print(f"Wrote {REMOTION_TIMING}")


if __name__ == "__main__":
    main()
