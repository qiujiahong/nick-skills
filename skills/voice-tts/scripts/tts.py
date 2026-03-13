#!/usr/bin/env python3
"""
火山引擎语音合成 (TTS) 脚本
支持声音复刻音色、语速/语调/情感控制
支持分段模式：不同段落使用不同语气/语速/语调
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

API_URL = "https://openspeech.bytedance.com/api/v1/tts"

EMOTIONS = {"happy", "sad", "angry", "scare", "hate", "surprise", "neutral"}


def synthesize_one(text: str, voice_type: str, cluster: str, encoding: str,
                   speed: float, pitch: float, emotion: str) -> bytes:
    """Call TTS API for a single segment and return audio bytes."""
    api_key = os.environ.get("NICK_SKILLS_ENV_VOICE_TTS_API_KEY")
    if not api_key:
        print("Error: NICK_SKILLS_ENV_VOICE_TTS_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    audio_config = {
        "voice_type": voice_type,
        "encoding": encoding,
        "speed_ratio": speed,
        "pitch_ratio": pitch,
    }
    if emotion:
        audio_config["emotion"] = emotion

    payload = {
        "app": {"cluster": cluster},
        "user": {"uid": "openclaw_tts"},
        "audio": audio_config,
        "request": {
            "reqid": uuid.uuid4().hex,
            "text": text,
            "operation": "query",
        },
    }

    resp = requests.post(
        API_URL,
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )

    if resp.status_code != 200:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        print(resp.text[:500], file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    code = result.get("code")

    if code != 3000:
        print(f"Error: API code {code}, message: {result.get('message', 'unknown')}", file=sys.stderr)
        sys.exit(1)

    data = result.get("data")
    if not data:
        print("Error: No audio data in response", file=sys.stderr)
        sys.exit(1)

    return base64.b64decode(data)


def parse_segments(text: str, default_speed: float, default_pitch: float, default_emotion: str):
    """
    Parse text with inline segment markers.

    Format: [emotion=happy speed=1.2 pitch=1.1]这是开心的文字[/]普通文字[emotion=sad speed=0.8]悲伤的文字[/]

    Segments without markers use default values.
    """
    pattern = r'\[([^\]]*?(?:emotion|speed|pitch)[^\]]*?)\](.*?)\[/\]'

    segments = []
    last_end = 0

    for match in re.finditer(pattern, text, re.DOTALL):
        # Text before this marker = default segment
        before = text[last_end:match.start()].strip()
        if before:
            segments.append({
                "text": before,
                "speed": default_speed,
                "pitch": default_pitch,
                "emotion": default_emotion,
            })

        # Parse marker attributes
        attrs = match.group(1)
        seg_text = match.group(2).strip()

        seg_emotion = default_emotion
        seg_speed = default_speed
        seg_pitch = default_pitch

        em = re.search(r'emotion=(\w+)', attrs)
        if em and em.group(1) in EMOTIONS:
            seg_emotion = em.group(1)
        sp = re.search(r'speed=([\d.]+)', attrs)
        if sp:
            seg_speed = float(sp.group(1))
        pi = re.search(r'pitch=([\d.]+)', attrs)
        if pi:
            seg_pitch = float(pi.group(1))

        if seg_text:
            segments.append({
                "text": seg_text,
                "speed": seg_speed,
                "pitch": seg_pitch,
                "emotion": seg_emotion,
            })

        last_end = match.end()

    # Remaining text after last marker
    remaining = text[last_end:].strip()
    if remaining:
        segments.append({
            "text": remaining,
            "speed": default_speed,
            "pitch": default_pitch,
            "emotion": default_emotion,
        })

    # If no markers found, return whole text as one segment
    if not segments:
        segments.append({
            "text": text,
            "speed": default_speed,
            "pitch": default_pitch,
            "emotion": default_emotion,
        })

    return segments


def concat_mp3(file_list: list, output: str):
    """Concatenate MP3 files using ffmpeg."""
    list_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for f in file_list:
        list_file.write(f"file '{f}'\n")
    list_file.close()

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file.name, "-c", "copy", output]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(list_file.name)

    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr[:500]}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="火山引擎语音合成")
    parser.add_argument("text", help="要合成的文本（支持分段标记）")
    parser.add_argument("-v", "--voice", default=None, help="音色 ID")
    parser.add_argument("-o", "--output", default="tts_output.mp3", help="输出文件路径")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="默认语速 (0.5-2.0)")
    parser.add_argument("-p", "--pitch", type=float, default=1.0, help="默认语调 (0.5-2.0)")
    parser.add_argument("--emotion", default=None,
                        choices=list(EMOTIONS),
                        help="默认情感标签")
    parser.add_argument("-e", "--encoding", default="mp3", choices=["mp3", "wav", "ogg_opus"], help="音频格式")
    parser.add_argument("-c", "--cluster", default=None, help="集群名称")

    args = parser.parse_args()

    voice = args.voice or os.environ.get("NICK_SKILLS_ENV_VOICE_TTS_VOICE_TYPE", "BV001_V2")
    cluster = args.cluster or os.environ.get("NICK_SKILLS_ENV_VOICE_TTS_CLUSTER", "volcano_icl")

    # Check if text contains segment markers
    has_markers = bool(re.search(r'\[([^\]]*?(?:emotion|speed|pitch)[^\]]*?)\]', args.text))

    if has_markers:
        segments = parse_segments(args.text, args.speed, args.pitch, args.emotion)
        print(f"Multi-segment mode: {len(segments)} segments", file=sys.stderr)

        tmp_files = []
        for i, seg in enumerate(segments):
            desc = f"[{i+1}/{len(segments)}]"
            if seg["emotion"]:
                desc += f" emotion={seg['emotion']}"
            if seg["speed"] != 1.0:
                desc += f" speed={seg['speed']}"
            if seg["pitch"] != 1.0:
                desc += f" pitch={seg['pitch']}"
            print(f"{desc} {seg['text'][:40]}{'...' if len(seg['text']) > 40 else ''}", file=sys.stderr)

            audio_data = synthesize_one(
                seg["text"], voice, cluster, args.encoding,
                seg["speed"], seg["pitch"], seg["emotion"],
            )

            tmp_path = tempfile.mktemp(suffix=f".{args.encoding}")
            with open(tmp_path, "wb") as f:
                f.write(audio_data)
            tmp_files.append(tmp_path)

        # Concatenate all segments
        if args.encoding == "mp3":
            concat_mp3(tmp_files, args.output)
        else:
            # For non-mp3, use ffmpeg filter
            inputs = " ".join(f"-i '{f}'" for f in tmp_files)
            filter_str = "".join(f"[{i}:a]" for i in range(len(tmp_files)))
            cmd = f"ffmpeg -y {inputs} -filter_complex '{filter_str}concat=n={len(tmp_files)}:v=0:a=1' '{args.output}'"
            subprocess.run(cmd, shell=True, capture_output=True)

        # Cleanup temp files
        for f in tmp_files:
            os.unlink(f)

        total_size = os.path.getsize(args.output)
        print(f"Audio saved to: {args.output} ({total_size} bytes, {len(segments)} segments)", file=sys.stderr)
    else:
        # Single segment mode
        print(f"Synthesizing with voice: {voice}, cluster: {cluster}", file=sys.stderr)
        if args.pitch != 1.0:
            print(f"Pitch: {args.pitch}", file=sys.stderr)
        if args.emotion:
            print(f"Emotion: {args.emotion}", file=sys.stderr)
        print(f"Text: {args.text[:80]}{'...' if len(args.text) > 80 else ''}", file=sys.stderr)

        audio_data = synthesize_one(
            args.text, voice, cluster, args.encoding,
            args.speed, args.pitch, args.emotion,
        )

        with open(args.output, "wb") as f:
            f.write(audio_data)

        print(f"Audio saved to: {args.output} ({len(audio_data)} bytes)", file=sys.stderr)

    print(args.output)


if __name__ == "__main__":
    main()
