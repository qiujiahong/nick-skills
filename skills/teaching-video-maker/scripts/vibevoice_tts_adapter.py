#!/usr/bin/env python3
"""Command adapter from teaching-video-maker scenes to local VibeVoice."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def normalize_for_vibevoice(text: str) -> str:
    replacements = {
        "，": ",",
        "。": ".",
        "；": ";",
        "：": ":",
        "、": ",",
        "（": "(",
        "）": ")",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "？": "?",
        "！": "!",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return " ".join(text.split())


def choose_speaker(language: str, voice_ref: str, speaker_id: str) -> str:
    if voice_ref:
        return "authorized-reference"
    if speaker_id:
        return speaker_id
    if language.lower().startswith("zh"):
        return "Bowen"
    return "Alice"


def install_voice_ref(source_dir: Path, voice_ref: str) -> None:
    if not voice_ref:
        return
    ref = Path(voice_ref).expanduser().resolve()
    if not ref.exists():
        raise FileNotFoundError(f"Voice reference does not exist: {ref}")
    if ref.suffix.lower() != ".wav":
        raise ValueError("VibeVoice reference audio must be a .wav file for this adapter.")

    voices_dir = source_dir / "demo" / "voices"
    voices_dir.mkdir(parents=True, exist_ok=True)
    target = voices_dir / "authorized-reference.wav"
    if target.exists() or target.is_symlink():
        target.unlink()
    try:
        target.symlink_to(ref)
    except OSError:
        shutil.copy2(ref, target)


def find_generated_wav(output_dir: Path, text_stem: str) -> Path:
    expected = output_dir / f"{text_stem}_generated.wav"
    if expected.exists():
        return expected
    matches = sorted(output_dir.glob("*_generated.wav"), key=lambda path: path.stat().st_mtime, reverse=True)
    if matches:
        return matches[0]
    raise FileNotFoundError(f"VibeVoice did not create a generated wav in {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one teaching-video scene with local VibeVoice.")
    parser.add_argument("--source-dir", default=os.environ.get("VIBEVOICE_SOURCE_DIR"))
    parser.add_argument("--model", default=os.environ.get("VIBEVOICE_MODEL", "microsoft/VibeVoice-1.5B"))
    parser.add_argument("--text-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--language", default=os.environ.get("VIBEVOICE_LANGUAGE", "zh"))
    parser.add_argument("--speaker-id", default=os.environ.get("VIBEVOICE_SPEAKER_ID", ""))
    parser.add_argument("--voice-ref", default=os.environ.get("VIBEVOICE_VOICE_REF", ""))
    parser.add_argument("--device", default=os.environ.get("VIBEVOICE_DEVICE", ""))
    parser.add_argument("--cfg-scale", default=os.environ.get("VIBEVOICE_CFG_SCALE", "1.3"))
    parser.add_argument("--seed", default=os.environ.get("VIBEVOICE_SEED", "1227"))
    parser.add_argument("--disable-prefill", action="store_true")
    args = parser.parse_args()

    if not args.source_dir:
        raise SystemExit("Set --source-dir or VIBEVOICE_SOURCE_DIR to the local VibeVoice checkout.")

    source_dir = Path(args.source_dir).expanduser().resolve()
    inference = source_dir / "demo" / "inference_from_file.py"
    if not inference.exists():
        raise FileNotFoundError(f"Missing VibeVoice inference script: {inference}")

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    install_voice_ref(source_dir, args.voice_ref)

    raw_text = Path(args.text_file).read_text(encoding="utf-8")
    speaker = choose_speaker(args.language, args.voice_ref, args.speaker_id)
    normalized = normalize_for_vibevoice(raw_text)

    with tempfile.TemporaryDirectory(prefix="teaching-video-vibevoice-") as tmp:
        tmp_dir = Path(tmp)
        scene_text = tmp_dir / f"{output.stem}.txt"
        generated_dir = tmp_dir / "out"
        scene_text.write_text(f"Speaker 1: {normalized}\n", encoding="utf-8")

        cmd = [
            sys.executable,
            str(inference),
            "--model_path",
            args.model,
            "--txt_path",
            str(scene_text),
            "--speaker_names",
            speaker,
            "--output_dir",
            str(generated_dir),
            "--cfg_scale",
            str(args.cfg_scale),
        ]
        if args.device:
            cmd.extend(["--device", args.device])
        if args.seed:
            cmd.extend(["--seed", str(args.seed)])
        if args.disable_prefill or os.environ.get("VIBEVOICE_DISABLE_PREFILL") == "1":
            cmd.append("--disable_prefill")

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{source_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
        subprocess.run(cmd, cwd=source_dir, env=env, check=True)

        generated = find_generated_wav(generated_dir, output.stem)
        shutil.copy2(generated, output)
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
