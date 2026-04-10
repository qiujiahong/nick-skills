#!/usr/bin/env python3
"""
WeChat Official Account publisher helper.

Features:
- Load local .env/.env.local automatically
- Get access token
- Upload article images and cover image materials
- Convert Markdown to WeChat-friendly HTML
- Create draft article
- Submit free publish
- Query publish status
"""
import argparse
import html
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def load_env_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_local_env() -> None:
    for name in (".env.local", ".env"):
        load_env_file(SKILL_DIR / name)


load_local_env()

BASE_URL = os.environ.get("WECHAT_MP_BASE_URL", "https://api.weixin.qq.com/cgi-bin").rstrip("/")
APP_ID = os.environ.get("WECHAT_MP_APP_ID", "")
APP_SECRET = os.environ.get("WECHAT_MP_APP_SECRET", "")
DEFAULT_AUTHOR = os.environ.get("WECHAT_MP_AUTHOR", "")
DEFAULT_THUMB_MEDIA_ID = os.environ.get("WECHAT_MP_THUMB_MEDIA_ID", "")

CONTAINER_STYLE = (
    "max-width: 677px; margin: 0 auto; color: #1f2329; "
    "font-size: 16px; line-height: 1.85; letter-spacing: 0.2px;"
)
H1_STYLE = (
    "margin: 0 0 22px; font-size: 30px; line-height: 1.28; "
    "font-weight: 700; color: #0f172a;"
)
H2_STYLE = (
    "margin: 34px 0 14px; font-size: 24px; line-height: 1.4; "
    "font-weight: 700; color: #0f172a;"
)
H3_STYLE = (
    "margin: 28px 0 12px; font-size: 20px; line-height: 1.45; "
    "font-weight: 700; color: #111827;"
)
P_STYLE = "margin: 0 0 18px; text-align: justify;"
LIST_STYLE = "margin: 0 0 18px 1.4em; padding: 0;"
LIST_ITEM_STYLE = "margin: 0 0 8px;"
BLOCKQUOTE_STYLE = (
    "margin: 22px 0; padding: 12px 16px; border-left: 4px solid #3b82f6; "
    "background: #f8fafc; color: #334155;"
)
CODE_BLOCK_STYLE = (
    "margin: 22px 0; padding: 14px 16px; border-radius: 12px; "
    "background: #0f172a; color: #e2e8f0; overflow-x: auto; "
    "font-size: 14px; line-height: 1.7;"
)
INLINE_CODE_STYLE = (
    "padding: 0.15em 0.38em; border-radius: 6px; background: #f1f5f9; "
    "font-size: 0.92em; font-family: Menlo, Consolas, monospace;"
)
FIGURE_STYLE = "margin: 28px 0; text-align: center;"
IMG_STYLE = "display: block; width: 100%; height: auto; border-radius: 12px;"
CAPTION_STYLE = "margin-top: 8px; font-size: 13px; color: #64748b;"
HR_STYLE = "margin: 30px 0; border: none; border-top: 1px solid #e2e8f0;"


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
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"errcode": -1, "errmsg": raw}


def http_multipart(url: str, files: Dict[str, Path], fields: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    body = bytearray()

    def append_text(name: str, value: str) -> None:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8")
        )

    def append_file(name: str, file_path: Path) -> None:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode("utf-8")
        )
        body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_path.read_bytes())
        body.extend(b"\r\n")

    for name, value in (fields or {}).items():
        append_text(name, value)
    for name, file_path in files.items():
        append_file(name, file_path)
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"errcode": -1, "errmsg": raw}


def get_access_token() -> str:
    require_credentials()
    query = urllib.parse.urlencode(
        {"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET}
    )
    url = f"{BASE_URL}/token?{query}"
    result = http_json(url)
    token = result.get("access_token")
    if not token:
        fail(f"ERROR: failed to get access token: {json.dumps(result, ensure_ascii=False)}")
    return token


def is_remote_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def is_image_target(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    suffix = Path(parsed.path or value).suffix.lower()
    return suffix in IMAGE_SUFFIXES


def resolve_local_path(base_dir: Path, raw_target: str) -> Optional[Path]:
    target = raw_target.strip()
    if not target or is_remote_url(target):
        return None
    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()
    return candidate if candidate.exists() else None


def upload_article_image(token: str, file_path: str) -> Dict[str, Any]:
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        fail(f"ERROR: article image not found: {file_path}")
    url = f"{BASE_URL}/media/uploadimg?access_token={token}"
    result = http_multipart(url, files={"media": path})
    if not result.get("url"):
        fail(f"ERROR: failed to upload article image: {json.dumps(result, ensure_ascii=False)}")
    return result


def upload_thumb_image(token: str, file_path: str) -> Dict[str, Any]:
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        fail(f"ERROR: thumb image not found: {file_path}")
    url = f"{BASE_URL}/material/add_material?access_token={token}&type=image"
    result = http_multipart(url, files={"media": path})
    if not result.get("media_id"):
        fail(f"ERROR: failed to upload thumb image: {json.dumps(result, ensure_ascii=False)}")
    return result


def inline_markdown_to_html(text: str) -> str:
    pieces: List[str] = []
    for segment in re.split(r"(`[^`]+`)", text):
        if not segment:
            continue
        if segment.startswith("`") and segment.endswith("`"):
            code = html.escape(segment[1:-1])
            pieces.append(f'<code style="{INLINE_CODE_STYLE}">{code}</code>')
            continue
        escaped = html.escape(segment)
        escaped = re.sub(
            r"\[(.+?)\]\((https?://[^\s)]+)\)",
            r'<a href="\2" style="color: #2563eb; text-decoration: none;">\1</a>',
            escaped,
        )
        escaped = re.sub(
            r"&lt;(https?://[^&]+)&gt;",
            r'<a href="\1" style="color: #2563eb; text-decoration: none;">\1</a>',
            escaped,
        )
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
        pieces.append(escaped)
    return "".join(pieces)


def render_figure(alt: str, src: str) -> str:
    caption = html.escape(alt.strip())
    parts = [f'<figure style="{FIGURE_STYLE}">']
    parts.append(f'<img src="{html.escape(src, quote=True)}" alt="{caption}" style="{IMG_STYLE}">')
    if caption:
        parts.append(f'<figcaption style="{CAPTION_STYLE}">{caption}</figcaption>')
    parts.append("</figure>")
    return "".join(parts)


def markdown_to_html(text: str) -> str:
    lines = text.splitlines()
    out: List[str] = [f'<section style="{CONTAINER_STYLE}">']
    paragraph_lines: List[str] = []
    blockquote_lines: List[str] = []
    list_items: List[str] = []
    list_kind: Optional[str] = None
    code_lines: List[str] = []
    in_code_block = False

    def flush_paragraph() -> None:
        if paragraph_lines:
            content = "<br>".join(inline_markdown_to_html(line) for line in paragraph_lines)
            out.append(f'<p style="{P_STYLE}">{content}</p>')
            paragraph_lines.clear()

    def flush_blockquote() -> None:
        if blockquote_lines:
            content = "<br>".join(inline_markdown_to_html(line) for line in blockquote_lines)
            out.append(f'<blockquote style="{BLOCKQUOTE_STYLE}">{content}</blockquote>')
            blockquote_lines.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_items and list_kind:
            tag = "ol" if list_kind == "ol" else "ul"
            out.append(f'<{tag} style="{LIST_STYLE}">')
            for item in list_items:
                out.append(f'<li style="{LIST_ITEM_STYLE}">{inline_markdown_to_html(item)}</li>')
            out.append(f"</{tag}>")
            list_items.clear()
            list_kind = None

    def flush_code_block() -> None:
        nonlocal in_code_block
        if in_code_block:
            code = html.escape("\n".join(code_lines))
            out.append(f'<pre style="{CODE_BLOCK_STYLE}"><code>{code}</code></pre>')
            code_lines.clear()
            in_code_block = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_blockquote()
            flush_list()
            if in_code_block:
                flush_code_block()
            else:
                in_code_block = True
                code_lines.clear()
            continue

        if in_code_block:
            code_lines.append(raw_line)
            continue

        if not stripped:
            flush_paragraph()
            flush_blockquote()
            flush_list()
            continue

        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            flush_blockquote()
            flush_list()
            out.append(render_figure(image_match.group(1), image_match.group(2).strip()))
            continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush_paragraph()
            flush_blockquote()
            flush_list()
            out.append(f'<hr style="{HR_STYLE}">')
            continue

        heading_match = re.fullmatch(r"(#{1,3})\s+(.+)", stripped)
        if heading_match:
            flush_paragraph()
            flush_blockquote()
            flush_list()
            level = len(heading_match.group(1))
            content = inline_markdown_to_html(heading_match.group(2).strip())
            if level == 1:
                out.append(f'<h1 style="{H1_STYLE}">{content}</h1>')
            elif level == 2:
                out.append(f'<h2 style="{H2_STYLE}">{content}</h2>')
            else:
                out.append(f'<h3 style="{H3_STYLE}">{content}</h3>')
            continue

        blockquote_match = re.fullmatch(r">\s?(.*)", stripped)
        if blockquote_match:
            flush_paragraph()
            flush_list()
            blockquote_lines.append(blockquote_match.group(1))
            continue

        ul_match = re.fullmatch(r"[-*]\s+(.+)", stripped)
        ol_match = re.fullmatch(r"\d+\.\s+(.+)", stripped)
        if ul_match or ol_match:
            flush_paragraph()
            flush_blockquote()
            current_kind = "ol" if ol_match else "ul"
            item = (ol_match or ul_match).group(1)
            if list_kind and list_kind != current_kind:
                flush_list()
            list_kind = current_kind
            list_items.append(item)
            continue

        flush_blockquote()
        flush_list()
        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_blockquote()
    flush_list()
    flush_code_block()
    out.append("</section>")
    return "\n".join(out)


def replace_local_markdown_images(
    text: str,
    base_dir: Path,
    token: Optional[str],
    upload_local_images: bool,
) -> str:
    cache: Dict[str, str] = {}

    def resolve_or_keep(target: str) -> str:
        local_path = resolve_local_path(base_dir, target)
        if not local_path or not is_image_target(str(local_path)):
            return target
        key = str(local_path)
        if key not in cache:
            cache[key] = (
                upload_article_image(token, key)["url"] if upload_local_images and token else key
            )
        return cache[key]

    def replace_image(match: re.Match[str]) -> str:
        alt, target = match.group(1), match.group(2).strip()
        if is_remote_url(target):
            return match.group(0)
        resolved = resolve_local_path(base_dir, target)
        if not resolved or not is_image_target(str(resolved)):
            return match.group(0)
        return f"![{alt}]({resolve_or_keep(target)})"

    def replace_link(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2).strip()
        if is_remote_url(target):
            return match.group(0)
        resolved = resolve_local_path(base_dir, target)
        if not resolved or not is_image_target(str(resolved)):
            return match.group(0)
        return f"![{label}]({resolve_or_keep(target)})"

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_image, text)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, text)


def replace_local_html_images(
    text: str,
    base_dir: Path,
    token: Optional[str],
    upload_local_images: bool,
) -> str:
    cache: Dict[str, str] = {}

    def replace_src(match: re.Match[str]) -> str:
        prefix, quote, target = match.group(1), match.group(2), match.group(3).strip()
        if is_remote_url(target):
            return match.group(0)
        resolved = resolve_local_path(base_dir, target)
        if not resolved or not is_image_target(str(resolved)):
            return match.group(0)
        key = str(resolved)
        if key not in cache:
            cache[key] = (
                upload_article_image(token, key)["url"] if upload_local_images and token else key
            )
        return f"{prefix}{quote}{cache[key]}{quote}"

    return re.sub(r"(<img\b[^>]*\bsrc=)(['\"])([^'\"]+)\2", replace_src, text, flags=re.IGNORECASE)


def load_content(
    path: str,
    fmt: str,
    token: Optional[str],
    upload_local_images: bool,
) -> str:
    source_path = Path(path).expanduser().resolve()
    content = source_path.read_text(encoding="utf-8")
    if fmt == "markdown":
        prepared = replace_local_markdown_images(content, source_path.parent, token, upload_local_images)
        return markdown_to_html(prepared)
    return replace_local_html_images(content, source_path.parent, token, upload_local_images)


def resolve_thumb_media_id(args: argparse.Namespace, token: str) -> str:
    if args.thumb_media_id:
        return args.thumb_media_id
    if args.thumb_file:
        return upload_thumb_image(token, args.thumb_file)["media_id"]
    if DEFAULT_THUMB_MEDIA_ID:
        return DEFAULT_THUMB_MEDIA_ID
    fail("ERROR: missing thumb media. Pass --thumb-media-id or --thumb-file, or set WECHAT_MP_THUMB_MEDIA_ID")


def maybe_write_rendered_html(content: str, output_path: str) -> None:
    target = Path(output_path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def render_content(args: argparse.Namespace) -> Dict[str, Any]:
    content = load_content(
        args.content_file,
        args.content_format,
        token=None,
        upload_local_images=False,
    )
    maybe_write_rendered_html(content, args.output)
    return {"errcode": 0, "output": str(Path(args.output).expanduser())}


def create_draft(args: argparse.Namespace) -> Dict[str, Any]:
    token = get_access_token()
    thumb_media_id = resolve_thumb_media_id(args, token)
    content = load_content(
        args.content_file,
        args.content_format,
        token=token,
        upload_local_images=not args.skip_upload_local_images,
    )
    if args.rendered_html_output:
        maybe_write_rendered_html(content, args.rendered_html_output)

    article = {
        "title": args.title,
        "author": args.author or DEFAULT_AUTHOR,
        "digest": args.digest or "",
        "content": content,
        "content_source_url": args.content_source_url or "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": int(bool(args.need_open_comment)),
        "only_fans_can_comment": int(bool(args.only_fans_can_comment)),
    }
    payload = {"articles": [article]}
    url = f"{BASE_URL}/draft/add?access_token={token}"
    return http_json(url, method="POST", payload=payload)


def upload_article_image_command(args: argparse.Namespace) -> Dict[str, Any]:
    token = get_access_token()
    return upload_article_image(token, args.file)


def upload_thumb_image_command(args: argparse.Namespace) -> Dict[str, Any]:
    token = get_access_token()
    return upload_thumb_image(token, args.file)


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
    draft.add_argument("--thumb-file", default="")
    draft.add_argument("--rendered-html-output", default="")
    draft.add_argument("--skip-upload-local-images", action="store_true")
    draft.add_argument("--need-open-comment", action="store_true")
    draft.add_argument("--only-fans-can-comment", action="store_true")
    draft.set_defaults(func=create_draft)

    render = sub.add_parser("render-content", help="Render markdown/html to WeChat-friendly HTML locally")
    render.add_argument("--content-file", required=True)
    render.add_argument("--content-format", choices=["html", "markdown"], default="html")
    render.add_argument("--output", required=True)
    render.set_defaults(func=render_content)

    article_image = sub.add_parser("upload-article-image", help="Upload an in-body article image")
    article_image.add_argument("--file", required=True)
    article_image.set_defaults(func=upload_article_image_command)

    thumb_image = sub.add_parser("upload-thumb-image", help="Upload a cover image and get thumb media_id")
    thumb_image.add_argument("--file", required=True)
    thumb_image.set_defaults(func=upload_thumb_image_command)

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
