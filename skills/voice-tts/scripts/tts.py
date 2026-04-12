#!/usr/bin/env python3
"""Local VibeVoice TTS wrapper."""

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ENSURE_SCRIPT = SCRIPT_DIR / "ensure_vibevoice.sh"
ENV_FILE = Path(os.environ.get("VIBEVOICE_ENV_FILE", Path.home() / ".cache/nick-skills/vibevoice/env.sh"))
MARKER_RE = re.compile(r"\[([^\]]*?(?:emotion|speed|pitch)[^\]]*?)\](.*?)\[/\]", re.DOTALL)


def read_text(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.text:
        return args.text
    return sys.stdin.read()


def strip_voice_director_markers(text: str) -> str:
    text = MARKER_RE.sub(lambda match: match.group(2), text)
    return text.strip()


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


def command_looks_usable(command: str, source_dir: str) -> bool:
    if not command or not source_dir or not Path(source_dir).exists():
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    script_paths = [Path(token) for token in tokens if token.endswith(".py") and "{" not in token]
    return all(path.exists() for path in script_paths)


def ensure_local_vibevoice(env: dict[str, str], skip_ensure: bool) -> dict[str, str]:
    merged = dict(env)
    merged.update(parse_env_file(ENV_FILE))
    if command_looks_usable(merged.get("VIBEVOICE_TTS_CMD", ""), merged.get("VIBEVOICE_SOURCE_DIR", "")):
        return merged
    if skip_ensure:
        raise SystemExit("Local VibeVoice is not configured. Run scripts/ensure_vibevoice.sh first.")
    subprocess.run([str(ENSURE_SCRIPT)], check=True, env=env)
    merged = dict(env)
    merged.update(parse_env_file(ENV_FILE))
    if not merged.get("VIBEVOICE_TTS_CMD"):
        raise SystemExit(f"{ENV_FILE} did not define VIBEVOICE_TTS_CMD")
    return merged


def run_vibevoice(text: str, wav_output: Path, args: argparse.Namespace, env: dict[str, str]) -> None:
    wav_output.parent.mkdir(parents=True, exist_ok=True)
    render_env = dict(env)
    if args.cfg_scale:
        render_env["VIBEVOICE_CFG_SCALE"] = str(args.cfg_scale)
    if args.device:
        render_env["VIBEVOICE_DEVICE"] = args.device

    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as tmp:
        tmp.write(text)
        text_file = tmp.name

    values = {
        "model": args.model or env.get("VIBEVOICE_MODEL", "microsoft/VibeVoice-1.5B"),
        "text": text,
        "text_file": text_file,
        "output": str(wav_output),
        "voice_ref": args.voice_ref or env.get("VIBEVOICE_VOICE_REF", ""),
        "speaker_id": args.speaker_id or args.voice or env.get("VIBEVOICE_SPEAKER_ID", ""),
        "language": args.language or env.get("VIBEVOICE_LANGUAGE", "zh"),
        "seed": str(args.seed or env.get("VIBEVOICE_SEED", "1227")),
    }
    try:
        command = env["VIBEVOICE_TTS_CMD"].format(**{key: shlex.quote(value) for key, value in values.items()})
        subprocess.run(command, shell=True, check=True, env=render_env)
    finally:
        Path(text_file).unlink(missing_ok=True)

    if not wav_output.exists():
        raise RuntimeError(f"VibeVoice did not create {wav_output}")


def convert_audio(wav_input: Path, output: Path, audio_format: str) -> None:
    if audio_format == "wav":
        if wav_input != output:
            output.write_bytes(wav_input.read_bytes())
        return

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(wav_input),
        str(output),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local VibeVoice text-to-speech")
    parser.add_argument("text", nargs="?", help="Text to synthesize. Reads stdin when omitted.")
    parser.add_argument("-f", "--file", help="Read text from a UTF-8 file")
    parser.add_argument("-o", "--output", default="tts_output.wav", help="Output audio path")
    parser.add_argument("-e", "--encoding", choices=["wav", "mp3"], help="Output format")
    parser.add_argument("--format", choices=["wav", "mp3"], help="Output format")
    parser.add_argument("-v", "--voice", help="Alias for --speaker-id")
    parser.add_argument("--speaker-id", help="VibeVoice speaker preset, e.g. Bowen or Alice")
    parser.add_argument("--voice-ref", help="Authorized local .wav reference audio")
    parser.add_argument("--language", default=None, help="Language hint, default zh")
    parser.add_argument("--model", default=None, help="Model repo, default microsoft/VibeVoice-1.5B")
    parser.add_argument("--seed", default=None, help="Stable generation seed")
    parser.add_argument("--cfg-scale", default=None, help="VibeVoice cfg_scale")
    parser.add_argument("--device", default=None, help="VibeVoice device override")
    parser.add_argument("--keep-markers", action="store_true", help="Do not strip voice-director markers")
    parser.add_argument("--no-ensure", action="store_true", help="Do not run ensure_vibevoice.sh automatically")
    parser.add_argument("-s", "--speed", type=float, default=None, help="Accepted for old callers; ignored")
    parser.add_argument("-p", "--pitch", type=float, default=None, help="Accepted for old callers; ignored")
    parser.add_argument("--emotion", default=None, help="Accepted for old callers; ignored")
    parser.add_argument("-c", "--cluster", default=None, help="Accepted for old callers; ignored")
    args = parser.parse_args()

    text = read_text(args).strip()
    if not text:
        raise SystemExit("No text provided")
    if not args.keep_markers:
        text = strip_voice_director_markers(text)

    output = Path(args.output).expanduser().resolve()
    audio_format = args.format or args.encoding or output.suffix.lower().lstrip(".") or "wav"
    if audio_format not in {"wav", "mp3"}:
        raise SystemExit("Only wav and mp3 outputs are supported by the local VibeVoice wrapper.")

    env = ensure_local_vibevoice(os.environ.copy(), args.no_ensure)
    if args.speed or args.pitch or args.emotion or args.cluster:
        print("Note: local VibeVoice does not use speed/pitch/emotion/cluster controls.", file=sys.stderr)

    if audio_format == "wav":
        run_vibevoice(text, output, args, env)
    else:
        with tempfile.TemporaryDirectory(prefix="voice-tts-") as tmp:
            wav_output = Path(tmp) / "tts.wav"
            run_vibevoice(text, wav_output, args, env)
            output.parent.mkdir(parents=True, exist_ok=True)
            convert_audio(wav_output, output, audio_format)

    print(output)


if __name__ == "__main__":
    main()
