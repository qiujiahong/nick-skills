#!/usr/bin/env python3
"""
AI Image Generation Script
Uses Gemini Flash Image Preview model via generateContent API.
Falls back to curl for better compatibility with some upstream gateways.
"""
import os
import sys
import json
import base64
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API_KEY = os.environ.get("IMAGE_GEN_API_KEY", "")
BASE_URL = os.environ.get("IMAGE_GEN_BASE_URL", "https://api.apiyi.com")
DEFAULT_MODEL = os.environ.get("IMAGE_GEN_MODEL", "gemini-3.1-flash-image-preview")
DEFAULT_ASPECT_RATIO = os.environ.get("IMAGE_GEN_ASPECT_RATIO", "16:9")
DEFAULT_IMAGE_SIZE = os.environ.get("IMAGE_GEN_IMAGE_SIZE", "2K")


def _call_api_with_curl(url: str, payload: dict) -> dict:
    curl_bin = shutil.which("curl")
    if not curl_bin:
        raise RuntimeError("curl not found")

    command = [
        curl_bin,
        "--silent",
        "--show-error",
        "--max-time",
        "300",
        url,
        "-H",
        f"Authorization: Bearer {API_KEY}",
        "-H",
        "Content-Type: application/json",
        "--data",
        json.dumps(payload, ensure_ascii=False),
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "curl request failed")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"invalid JSON response: {e}; body={result.stdout[:2000]}")


def _call_api_with_urllib(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        raise RuntimeError(f"HTTP {e.code}: {body[:2000]}")
    except URLError as e:
        raise RuntimeError(f"network error: {e}")


def call_api(url: str, payload: dict) -> dict:
    errors = []

    try:
        return _call_api_with_curl(url, payload)
    except Exception as e:
        errors.append(f"curl failed: {e}")

    try:
        return _call_api_with_urllib(url, payload)
    except Exception as e:
        errors.append(f"urllib failed: {e}")

    raise RuntimeError("; ".join(errors))


def generate_image(
    prompt: str,
    model: str = DEFAULT_MODEL,
    output_path: Optional[str] = None,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    image_size: str = DEFAULT_IMAGE_SIZE,
) -> str:
    """Generate image from text prompt."""

    if not API_KEY:
        print("ERROR: IMAGE_GEN_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    url = f"{BASE_URL}/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
                "imageSize": image_size,
            },
        },
    }

    print(f"Generating image with model: {model}", file=sys.stderr)
    print(f"Aspect ratio: {aspect_ratio}, image size: {image_size}", file=sys.stderr)
    print(f"Prompt: {prompt[:120]}...", file=sys.stderr)

    try:
        result = call_api(url, payload)
    except Exception as e:
        print(f"ERROR: API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        parts = result["candidates"][0]["content"]["parts"]
    except Exception:
        print(f"ERROR: Unexpected response structure: {result}", file=sys.stderr)
        sys.exit(1)

    image_data = None
    for part in parts:
        if "inlineData" in part and part["inlineData"].get("data"):
            image_data = part["inlineData"]
            break

    if not image_data:
        print(f"ERROR: No image found in response: {result}", file=sys.stderr)
        sys.exit(1)

    img_bytes = base64.b64decode(image_data["data"])
    mime_type = image_data.get("mimeType", "image/png")
    ext = mime_type.split("/")[-1] if "/" in mime_type else "png"

    out_file = Path(output_path) if output_path else Path.cwd() / f"generated_image.{ext}"
    out_file.write_bytes(img_bytes)

    print(f"Image saved to: {out_file}", file=sys.stderr)
    print(str(out_file))
    return str(out_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate image with Gemini Flash Image Preview")
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="Model to use")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--aspect-ratio", default=DEFAULT_ASPECT_RATIO, help="Aspect ratio, e.g. 1:1, 3:2, 16:9")
    parser.add_argument("--image-size", default=DEFAULT_IMAGE_SIZE, help="Image size, e.g. standard, 2K, 4K")
    args = parser.parse_args()

    generate_image(
        prompt=args.prompt,
        model=args.model,
        output_path=args.output,
        aspect_ratio=args.aspect_ratio,
        image_size=args.image_size,
    )
