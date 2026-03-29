#!/usr/bin/env python3
"""
WeChat Official Account publisher helper.

Features:
- Get access token
- Create draft article
- Submit free publish
- Query publish status
- Accept markdown/html content file
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

BASE_URL = os.environ.get("WECHAT_MP_BASE_URL", "https://api.weixin.qq.com/cgi-bin").rstrip("/")
APP_ID = os.environ.get("WECHAT_MP_APP_ID", "")
APP_SECRET = os.environ.get("WECHAT_MP_APP_SECRET", "")
DEFAULT_AUTHOR = os.environ.get("WECHAT_MP_AUTHOR", "")
DEFAULT_THUMB_MEDIA_ID = os.environ.get("WECHAT_MP_THUMB_MEDIA_ID", "")


def fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def require_credentials() -> None:
    if not APP_ID or not APP_SECRET:
        fail("ERROR: missing WECHAT_MP_APP_ID or WECHAT_MP_APP_SECRET")


def http_json(url: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def get_access_token() -> str:
    require_credentials()
    query = urllib.parse.urlencode({
        "grant_type": "client_credential",
        "appid": APP_ID,
        "secret": APP_SECRET,
    })
    url = f"{BASE_URL}/token?{query}"
    result = http_json(url)
    token = result.get("access_token")
    if not token:
        fail(f"ERROR: failed to get access token: {json.dumps(result, ensure_ascii=False)}")
    return token


def markdown_to_html(text: str) -> str:
    lines = text.splitlines()
    out = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_list()
            continue

        if line.startswith("### "):
            close_list()
            out.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
            continue
        if line.startswith("## "):
            close_list()
            out.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
            continue
        if line.startswith("# "):
            close_list()
            out.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
            continue
        if line.startswith("- ") or line.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_markdown_to_html(line[2:].strip())}</li>")
            continue

        close_list()
        out.append(f"<p>{inline_markdown_to_html(line.strip())}</p>")

    close_list()
    return "\n".join(out)


def inline_markdown_to_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((https?://[^\s]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def load_content(path: str, fmt: str) -> str:
    content = Path(path).read_text(encoding="utf-8")
    if fmt == "markdown":
        return markdown_to_html(content)
    return content


def create_draft(args: argparse.Namespace) -> Dict[str, Any]:
    token = get_access_token()
    content = load_content(args.content_file, args.content_format)
    article = {
        "title": args.title,
        "author": args.author or DEFAULT_AUTHOR,
        "digest": args.digest or "",
        "content": content,
        "content_source_url": args.content_source_url or "",
        "thumb_media_id": args.thumb_media_id or DEFAULT_THUMB_MEDIA_ID,
        "need_open_comment": int(bool(args.need_open_comment)),
        "only_fans_can_comment": int(bool(args.only_fans_can_comment)),
    }
    payload = {"articles": [article]}
    url = f"{BASE_URL}/draft/add?access_token={token}"
    return http_json(url, method="POST", payload=payload)


def publish(args: argparse.Namespace) -> Dict[str, Any]:
    token = get_access_token()
    payload = {"media_id": args.media_id}
    url = f"{BASE_URL}/freepublish/submit?access_token={token}"
    return http_json(url, method="POST", payload=payload)


def get_publish_status(args: argparse.Namespace) -> Dict[str, Any]:
    token = get_access_token()
    payload = {"publish_id": args.publish_id}
    url = f"{BASE_URL}/freepublish/get?access_token={token}"
    return http_json(url, method="POST", payload=payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WeChat MP publisher helper")
    sub = parser.add_subparsers(dest="command", required=True)

    draft = sub.add_parser("create-draft", help="Create a draft article")
    draft.add_argument("--title", required=True)
    draft.add_argument("--author", default="")
    draft.add_argument("--digest", default="")
    draft.add_argument("--content-file", required=True)
    draft.add_argument("--content-format", choices=["html", "markdown"], default="html")
    draft.add_argument("--content-source-url", default="")
    draft.add_argument("--thumb-media-id", default="")
    draft.add_argument("--need-open-comment", action="store_true")
    draft.add_argument("--only-fans-can-comment", action="store_true")
    draft.set_defaults(func=create_draft)

    pub = sub.add_parser("publish", help="Submit a draft for publishing")
    pub.add_argument("--media-id", required=True)
    pub.set_defaults(func=publish)

    status = sub.add_parser("get-publish-status", help="Get publish status")
    status.add_argument("--publish-id", required=True)
    status.set_defaults(func=get_publish_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    result = args.func(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("errcode", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
