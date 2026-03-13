#!/usr/bin/env python3
"""
火山引擎语音合成 (TTS) 脚本
支持声音复刻音色、语速/语调/情感控制、SSML
"""

import argparse
import base64
import json
import os
import sys
import uuid

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

API_URL = "https://openspeech.bytedance.com/api/v1/tts"


def synthesize(text: str, voice_type: str, cluster: str, encoding: str,
               speed: float, pitch: float, emotion: str, ssml: bool) -> bytes:
    """Call TTS API and return audio bytes."""
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

    request_config = {
        "reqid": uuid.uuid4().hex,
        "text": text,
        "operation": "query"
    }
    if ssml:
        request_config["text_type"] = "ssml"

    payload = {
        "app": {"cluster": cluster},
        "user": {"uid": "openclaw_tts"},
        "audio": audio_config,
        "request": request_config,
    }

    resp = requests.post(
        API_URL,
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
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


def main():
    parser = argparse.ArgumentParser(description="火山引擎语音合成")
    parser.add_argument("text", help="要合成的文本（或 SSML 内容）")
    parser.add_argument("-v", "--voice", default=None, help="音色 ID")
    parser.add_argument("-o", "--output", default="tts_output.mp3", help="输出文件路径")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="语速 (0.5-2.0)")
    parser.add_argument("-p", "--pitch", type=float, default=1.0, help="语调 (0.5-2.0)，>1 偏高，<1 偏低")
    parser.add_argument("--emotion", default=None, help="情感标签: happy/sad/angry/scare/hate/surprise/neutral")
    parser.add_argument("--ssml", action="store_true", help="输入文本为 SSML 格式")
    parser.add_argument("-e", "--encoding", default="mp3", choices=["mp3", "wav", "ogg_opus"], help="音频格式")
    parser.add_argument("-c", "--cluster", default=None, help="集群名称")

    args = parser.parse_args()

    voice = args.voice or os.environ.get("NICK_SKILLS_ENV_VOICE_TTS_VOICE_TYPE", "BV001_V2")
    cluster = args.cluster or os.environ.get("NICK_SKILLS_ENV_VOICE_TTS_CLUSTER", "volcano_icl")

    print(f"Synthesizing with voice: {voice}, cluster: {cluster}", file=sys.stderr)
    if args.pitch != 1.0:
        print(f"Pitch: {args.pitch}", file=sys.stderr)
    if args.emotion:
        print(f"Emotion: {args.emotion}", file=sys.stderr)
    if args.ssml:
        print("Mode: SSML", file=sys.stderr)
    print(f"Text: {args.text[:80]}{'...' if len(args.text) > 80 else ''}", file=sys.stderr)

    audio_data = synthesize(
        args.text, voice, cluster, args.encoding,
        args.speed, args.pitch, args.emotion, args.ssml,
    )

    with open(args.output, "wb") as f:
        f.write(audio_data)

    print(f"Audio saved to: {args.output} ({len(audio_data)} bytes)", file=sys.stderr)
    print(args.output)


if __name__ == "__main__":
    main()
