#!/usr/bin/env python3
"""
Tavily Search helper.
Supports multiple API keys via environment variables, random key selection,
and automatic fallback when a key is invalid, expired, rate-limited, or otherwise rejected.
"""
import argparse
import json
import os
import random
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple

DEFAULT_BASE_URL = os.environ.get("TAVILY_SEARCH_BASE_URL", "https://api.tavily.com").rstrip("/")
DEFAULT_TOPIC = "general"
DEFAULT_MAX_RESULTS = 5
RETRYABLE_STATUS_CODES = {401, 403, 429}


def parse_keys() -> List[str]:
    raw_multi = os.environ.get("TAVILY_API_KEYS", "")
    raw_single = os.environ.get("TAVILY_API_KEY", "")
    blob = "\n".join(part for part in [raw_multi, raw_single] if part)
    if not blob.strip():
        return []

    normalized = blob.replace(",", "\n").replace(";", "\n").replace(" ", "\n")
    keys = [item.strip() for item in normalized.splitlines() if item.strip()]

    deduped = []
    seen = set()
    for key in keys:
        if key not in seen:
            seen.add(key)
            deduped.append(key)
    return deduped


def parse_csv_list(value: str) -> List[str]:
    if not value:
        return []
    items = []
    for part in value.replace("\n", ",").split(","):
        item = part.strip()
        if item:
            items.append(item)
    return items


def build_payload(args: argparse.Namespace) -> dict:
    payload = {
        "query": args.query,
        "topic": args.topic,
        "max_results": args.max_results,
        "search_depth": args.search_depth,
        "include_answer": args.include_answer,
        "include_raw_content": args.include_raw_content,
        "include_images": args.include_images,
    }
    if args.days is not None:
        payload["days"] = args.days

    include_domains = parse_csv_list(args.include_domains)
    exclude_domains = parse_csv_list(args.exclude_domains)
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains
    return payload


def post_json(url: str, payload: dict, api_key: str) -> Tuple[int, dict]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status = getattr(resp, "status", 200)
            data = json.loads(resp.read().decode("utf-8"))
            return status, data
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        try:
            data = json.loads(raw) if raw else {"error": raw or str(e)}
        except json.JSONDecodeError:
            data = {"error": raw or str(e)}
        return e.code, data


def masked(key: str) -> str:
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


def search(args: argparse.Namespace) -> dict:
    keys = parse_keys()
    if not keys:
        print("ERROR: missing TAVILY_API_KEYS or TAVILY_API_KEY", file=sys.stderr)
        sys.exit(1)

    random.shuffle(keys)
    payload = build_payload(args)
    url = f"{args.base_url.rstrip('/')}/search"

    failures = []

    for index, key in enumerate(keys, start=1):
        print(f"Trying Tavily key {index}/{len(keys)}: {masked(key)}", file=sys.stderr)
        try:
            status, data = post_json(url, payload, key)
        except Exception as e:
            failures.append({
                "key": masked(key),
                "status": "exception",
                "error": str(e),
            })
            continue

        if 200 <= status < 300:
            result = {
                "ok": True,
                "used_key": masked(key),
                "topic": args.topic,
                "query": args.query,
                "response": data,
            }
            return result

        failure = {
            "key": masked(key),
            "status": status,
            "error": data,
        }
        failures.append(failure)

        if status not in RETRYABLE_STATUS_CODES:
            break

    return {
        "ok": False,
        "query": args.query,
        "topic": args.topic,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Tavily with multi-key fallback")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--topic", choices=["general", "news"], default=DEFAULT_TOPIC)
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    parser.add_argument("--search-depth", choices=["basic", "advanced"], default="basic")
    parser.add_argument("--days", type=int, default=None, help="Only used for news topic")
    parser.add_argument("--include-answer", action="store_true")
    parser.add_argument("--include-raw-content", action="store_true")
    parser.add_argument("--include-images", action="store_true")
    parser.add_argument("--include-domains", default="", help="Comma-separated domains to include, e.g. techcrunch.com,theverge.com")
    parser.add_argument("--exclude-domains", default="", help="Comma-separated domains to exclude")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output", help="Optional output JSON file path")
    args = parser.parse_args()

    result = search(args)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered + "\n", encoding="utf-8")
        print(str(out))
    else:
        print(rendered)

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
