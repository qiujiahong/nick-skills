#!/usr/bin/env python3
import argparse
import datetime as dt
import html
import json
import os
import random
import re
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Tuple

DEFAULT_QUERY = "金融 AI 应用 银行 券商 保险 资管 大模型 智能投研 风控 合规 AIAgent"
DEFAULT_TOPIC = "news"
DEFAULT_TOP_K = 20
DEFAULT_KEEP = 10
DEFAULT_BASE_URL = os.environ.get("TAVILY_SEARCH_BASE_URL", "https://api.tavily.com").rstrip("/")
RETRYABLE_STATUS_CODES = {401, 403, 429}
DEFAULT_QUERY_VARIANTS = [
    "金融 AI 应用 银行 券商 保险 资管 大模型 智能投研 风控 合规",
    "banking AI wealth management AI risk compliance AI financial services AI",
    "证券 券商 投研 AI 智能投顾 金融大模型",
    "保险 AI 风控 合规 智能客服 金融科技",
]

HIGH_VALUE_TERMS = {
    "银行": 8,
    "券商": 8,
    "证券": 7,
    "保险": 8,
    "资管": 8,
    "基金": 7,
    "投研": 10,
    "研究": 4,
    "交易": 7,
    "量化": 7,
    "风控": 10,
    "合规": 10,
    "监管": 9,
    "反洗钱": 9,
    "客服": 5,
    "运营": 5,
    "清算": 6,
    "支付": 6,
    "信贷": 7,
    "财富管理": 7,
    "投顾": 8,
    "agent": 5,
    "大模型": 7,
    "生成式ai": 6,
    "人工智能": 4,
    "ai": 3,
    "llm": 6,
    "模型": 3,
    "数据": 4,
    "知识库": 3,
    "自动化": 3,
    "效率": 3,
    "降本增效": 5,
}

LOW_VALUE_TERMS = {
    "融资": -4,
    "发布会": -2,
    "峰会": -2,
    "广告": -5,
    "营销": -5,
    "创业": -2,
    "游戏": -6,
    "娱乐": -6,
    "招聘": -4,
    "课程": -4,
    "教程": -3,
    "入门": -3,
    "测评": -2,
    "榜单": -2,
}

SOURCE_BONUS = {
    "bloomberg.com": 6,
    "reuters.com": 6,
    "ft.com": 6,
    "wsj.com": 5,
    "cnbc.com": 4,
    "finance.yahoo.com": 3,
    "mckinsey.com": 5,
    "pwc.com": 4,
    "ey.com": 4,
    "kpmg.com": 4,
    "deloitte.com": 4,
    "finextra.com": 5,
    "thefinancialbrand.com": 4,
    "ibsintelligence.com": 4,
    "techcrunch.com": 3,
    "theverge.com": 2,
    "hbr.org": 3,
    "www.scmp.com": 2,
}

FUN_FACTS = [
    "今天的 AI 趣味知识：Transformer 最早在 2017 年被系统提出，它最核心的突破之一，是让模型能同时关注一句话里的多个位置。",
    "大模型并不是像人一样‘理解’世界，它更像是在超大规模语料上学会了高维概率接龙，但这种接龙已经足够强到能辅助很多金融知识工作。",
    "对金融行业来说，真正有价值的 AI 往往不是最会聊天的模型，而是最能稳定接入数据、流程、权限和审计体系的那一个。",
    "很多金融 AI 应用的瓶颈并不在模型本身，而在数据治理、权限边界、可追溯性和人工复核机制。",
    "Agent 的关键不只是会调用工具，而是能在复杂流程里持续保持目标、上下文和风险约束。",
    "检索增强生成（RAG）之所以对金融场景重要，是因为它能把‘模型记忆’和‘机构最新知识库’结合起来。",
]


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


def masked(key: str) -> str:
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


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


def tavily_search(query: str, topic: str, max_results: int) -> dict:
    keys = parse_keys()
    if not keys:
        raise RuntimeError("missing TAVILY_API_KEYS or TAVILY_API_KEY")

    random.shuffle(keys)
    payload = {
        "query": query,
        "topic": topic,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False,
    }
    url = f"{DEFAULT_BASE_URL}/search"
    failures = []

    for key in keys:
        for attempt in range(1, 3):
            try:
                status, data = post_json(url, payload, key)
            except Exception as e:
                failures.append({
                    "key": masked(key),
                    "status": "exception",
                    "attempt": attempt,
                    "error": str(e),
                })
                if attempt < 2:
                    time.sleep(1.2 * attempt)
                    continue
                status, data = None, None

            if status is not None and 200 <= status < 300:
                return {
                    "ok": True,
                    "used_key": masked(key),
                    "query": query,
                    "topic": topic,
                    "response": data,
                }

            if status is not None:
                failures.append({"key": masked(key), "status": status, "attempt": attempt, "error": data})
                if status in RETRYABLE_STATUS_CODES and attempt < 2:
                    time.sleep(1.2 * attempt)
                    continue
                if status not in RETRYABLE_STATUS_CODES:
                    break
                if attempt >= 2:
                    break

    return {"ok": False, "query": query, "topic": topic, "failures": failures}


def multi_search(primary_query: str, topic: str, target_count: int) -> dict:
    queries = [primary_query] + [q for q in DEFAULT_QUERY_VARIANTS if q != primary_query]
    all_results = []
    search_runs = []

    per_query = max(6, min(10, target_count))
    for query in queries:
        result = tavily_search(query, topic, per_query)
        search_runs.append(result)
        if result.get("ok"):
            all_results.extend(result.get("response", {}).get("results", []))
        if len(dedupe_items(all_results)) >= target_count * 2:
            break

    merged = dedupe_items(all_results)
    ok = any(run.get("ok") for run in search_runs)
    return {
        "ok": ok,
        "query": primary_query,
        "topic": topic,
        "search_runs": search_runs,
        "response": {
            "results": merged,
        } if ok else {},
    }


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def hostname_from_url(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url or "")
    return (m.group(1).lower() if m else "").replace("www.", "")


def summarize_item(item: dict) -> str:
    content = normalize_text(item.get("content") or item.get("raw_content") or "")
    if not content:
        title = normalize_text(item.get("title") or "")
        return title[:120]
    if len(content) > 140:
        return content[:137].rstrip() + "..."
    return content


def score_item(item: dict) -> int:
    title_text = normalize_text(item.get("title") or "").lower()
    content_text = normalize_text(item.get("content") or item.get("raw_content") or "").lower()
    host = hostname_from_url(item.get("url") or "")
    text = " ".join([title_text, content_text, host])
    score = 0
    for term, weight in HIGH_VALUE_TERMS.items():
        if term.lower() in text:
            score += weight
    for term, weight in LOW_VALUE_TERMS.items():
        if term.lower() in text:
            score += weight

    for domain, bonus in SOURCE_BONUS.items():
        if host.endswith(domain.replace("www.", "")):
            score += bonus

    finance_terms = [
        "银行", "券商", "证券", "保险", "资管", "基金", "金融", "fintech", "financial", "bank", "banking", "asset management", "wealth", "broker", "trading", "investment"
    ]
    ai_terms = [
        "ai", "agent", "llm", "大模型", "人工智能", "模型", "机器学习", "automation", "copilot", "生成式"
    ]

    finance_hits = sum(1 for term in finance_terms if term.lower() in text)
    ai_hits = sum(1 for term in ai_terms if term.lower() in text)

    score += finance_hits * 3
    score += ai_hits * 2

    if finance_hits == 0:
        score -= 12
    if ai_hits == 0:
        score -= 8
    if finance_hits > 0 and ai_hits > 0:
        score += 10

    title = normalize_text(item.get("title") or "")
    if len(title) >= 18:
        score += 1
    if item.get("published_date"):
        score += 1
    return score


def dedupe_items(items: List[dict]) -> List[dict]:
    seen = set()
    output = []
    for item in items:
        url = normalize_text(item.get("url") or "")
        title = normalize_text(item.get("title") or "")
        key = (url.lower() or title.lower())
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def is_relevant_fin_ai_item(item: dict) -> bool:
    title = normalize_text(item.get("title") or "")
    content = normalize_text(item.get("content") or item.get("raw_content") or "")
    text = f"{title} {content}".lower()
    host = hostname_from_url(item.get("url") or "")

    finance_terms = [
        "银行", "券商", "证券", "保险", "资管", "基金", "金融", "fintech", "financial", "bank", "banking", "asset management", "wealth", "broker", "trading", "investment", "payments", "payment", "lending", "underwriting", "claims", "fraud"
    ]
    ai_terms = [
        "ai", "agent", "llm", "大模型", "人工智能", "模型", "机器学习", "automation", "copilot", "生成式", "genai"
    ]
    noise_terms = [
        "sports", "retail associate", "shopping assistant", "apartment portfolio", "telecom", "hospitality", "movie", "game", "fashion"
    ]
    noisy_hosts = {
        "marketbeat.com", "insidermonkey.com", "gurufocus.com", "cbsnews.com", "hospitalitynet.org", "developingtelecoms.com", "chainstoreage.com"
    }

    finance_hits = sum(1 for term in finance_terms if term.lower() in text)
    ai_hits = sum(1 for term in ai_terms if term.lower() in text)
    noise_hits = sum(1 for term in noise_terms if term in text)

    if host in noisy_hosts:
        return False
    if noise_hits > 0:
        return False
    if len(title) < 12:
        return False
    if finance_hits < 1 or ai_hits < 1:
        return False
    if len(content) < 80 and len(title) < 24:
        return False
    return True


def select_top_items(items: List[dict], keep: int) -> List[dict]:
    enriched = []
    for item in items:
        summary = summarize_item(item)
        score = score_item(item)
        enriched.append({
            "title": normalize_text(item.get("title") or "未命名资讯"),
            "summary": summary,
            "url": normalize_text(item.get("url") or ""),
            "source": hostname_from_url(item.get("url") or "") or "unknown",
            "published_date": item.get("published_date") or "",
            "score": score,
        })
    enriched.sort(key=lambda x: (x["score"], x["published_date"]), reverse=True)
    return enriched[:keep]


def build_overview(selected: List[dict], date_str: str, query: str) -> str:
    focus_terms = []
    for item in selected:
        text = (item["title"] + " " + item["summary"]).lower()
        for term in ["银行", "券商", "保险", "资管", "风控", "合规", "投研", "agent", "大模型", "监管"]:
            if term.lower() in text and term not in focus_terms:
                focus_terms.append(term)
    top_focus = "、".join(focus_terms[:5]) if focus_terms else "金融机构 AI 落地"
    return f"{date_str} 的金融 AI 简报共筛出 {len(selected)} 条高价值资讯，重点集中在 {top_focus} 等方向。整体看，真正值得金融机构关注的，不是泛 AI 热点，而是能映射到业务流程、监管要求和分析效率提升的实际应用。搜索主题为：{query}。"


def choose_fun_facts() -> List[str]:
    facts = random.sample(FUN_FACTS, k=3) if len(FUN_FACTS) >= 3 else FUN_FACTS
    return facts


def build_html(date_str: str, overview: str, items: List[dict], fun_facts: List[str]) -> str:
    cards = []
    for idx, item in enumerate(items, start=1):
        cards.append(f"""
        <section class=\"card\">
          <div class=\"meta\">#{idx} · {html.escape(item['source'])}</div>
          <h3><a href=\"{html.escape(item['url'])}\" target=\"_blank\">{html.escape(item['title'])}</a></h3>
          <p>{html.escape(item['summary'])}</p>
          <div class=\"link\"><a href=\"{html.escape(item['url'])}\" target=\"_blank\">查看原文</a></div>
        </section>
        """)

    facts_html = "".join(f"<li>{html.escape(fact)}</li>" for fact in fun_facts)

    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>金融 AI 资讯简报 - {html.escape(date_str)}</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --accent: #2563eb;
      --border: #e5e7eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: var(--bg); color: var(--text); }}
    .wrap {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 48px; }}
    .hero {{ background: linear-gradient(135deg, #0f172a, #1d4ed8); color: white; border-radius: 20px; padding: 28px; margin-bottom: 24px; }}
    .hero h1 {{ margin: 0 0 10px; font-size: 32px; }}
    .hero p {{ margin: 0; line-height: 1.7; color: rgba(255,255,255,0.92); }}
    .section-title {{ font-size: 22px; margin: 28px 0 14px; }}
    .grid {{ display: grid; gap: 16px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 18px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    .card h3 {{ margin: 8px 0 10px; font-size: 20px; line-height: 1.4; }}
    .card p {{ margin: 0; line-height: 1.7; color: #374151; }}
    .meta {{ font-size: 13px; color: var(--muted); }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .link {{ margin-top: 14px; font-size: 14px; }}
    .fun {{ background: #fffdf3; border: 1px solid #f5e6a8; }}
    .fun ul {{ margin: 0; padding-left: 22px; line-height: 1.8; }}
    .footer {{ margin-top: 28px; color: var(--muted); font-size: 13px; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <h1>金融 AI 资讯简报</h1>
      <p>{html.escape(overview)}</p>
    </div>

    <h2 class=\"section-title\">今日 10 条重点资讯</h2>
    <div class=\"grid\">
      {''.join(cards)}
    </div>

    <h2 class=\"section-title\">今日 AI 趣味知识</h2>
    <section class=\"card fun\">
      <ul>{facts_html}</ul>
    </section>

    <div class=\"footer\">本简报由 fin-ai-daily-brief 自动生成。</div>
  </div>
</body>
</html>
"""


def build_text(date_str: str, overview: str, items: List[dict], fun_facts: List[str]) -> str:
    lines = [
        f"金融 AI 资讯简报 - {date_str}",
        "",
        "总览：",
        overview,
        "",
        "今日 10 条重点资讯：",
    ]
    for idx, item in enumerate(items, start=1):
        lines.extend([
            f"{idx}. {item['title']}",
            f"   简述：{item['summary']}",
            f"   链接：{item['url']}",
            "",
        ])
    lines.append("今日 AI 趣味知识：")
    for fact in fun_facts:
        lines.append(f"- {fact}")
    lines.append("")
    lines.append("本简报由 fin-ai-daily-brief 自动生成。")
    return "\n".join(lines)


def parse_recipients(extra: List[str]) -> List[str]:
    raw = os.environ.get("FIN_AI_SUBSCRIBERS", "")
    parts = re.split(r"[,;\n]+", raw)
    emails = [p.strip() for p in parts if p.strip()]
    emails.extend([item.strip() for item in extra if item.strip()])
    deduped = []
    seen = set()
    for email in emails:
        key = email.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(email)
    return deduped


def send_email(subject: str, html_body: str, text_body: str, recipients: List[str]) -> None:
    host = os.environ.get("FIN_AI_SMTP_HOST", "")
    port = int(os.environ.get("FIN_AI_SMTP_PORT", "465"))
    user = os.environ.get("FIN_AI_SMTP_USER", "")
    password = os.environ.get("FIN_AI_SMTP_PASS", "")
    sender = os.environ.get("FIN_AI_SMTP_FROM", user)
    use_ssl = os.environ.get("FIN_AI_SMTP_USE_SSL", "true").strip().lower() not in {"0", "false", "no"}

    if not all([host, port, user, password, sender]):
        raise RuntimeError("SMTP config incomplete: FIN_AI_SMTP_HOST/PORT/USER/PASS/FROM required")
    if not recipients:
        raise RuntimeError("No recipients configured. Set FIN_AI_SUBSCRIBERS or use --recipient")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=60) as server:
            server.login(user, password)
            server.sendmail(sender, recipients, msg.as_string())
    else:
        with smtplib.SMTP(host, port, timeout=60) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(user, password)
            server.sendmail(sender, recipients, msg.as_string())


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and optionally email a financial AI daily brief")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--topic", default=DEFAULT_TOPIC, choices=["general", "news"])
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    parser.add_argument("--output-dir", default="./output")
    parser.add_argument("--recipient", action="append", default=[])
    parser.add_argument("--send-email", action="store_true")
    parser.add_argument("--subject", default="")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    search_result = multi_search(args.query, args.topic, args.top_k)
    (out_dir / "search-result.json").write_text(json.dumps(search_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not search_result.get("ok"):
        print(json.dumps(search_result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    raw_items = search_result.get("response", {}).get("results", [])
    deduped = dedupe_items(raw_items)
    filtered = [item for item in deduped if is_relevant_fin_ai_item(item)]
    selected = select_top_items(filtered, args.keep)

    candidates_view = []
    for item in filtered:
        candidates_view.append({
            "title": normalize_text(item.get("title") or ""),
            "summary": summarize_item(item),
            "url": normalize_text(item.get("url") or ""),
            "source": hostname_from_url(item.get("url") or ""),
            "score": score_item(item),
        })

    overview = build_overview(selected, args.date, args.query)
    fun_facts = choose_fun_facts()
    html_doc = build_html(args.date, overview, selected, fun_facts)
    text_doc = build_text(args.date, overview, selected, fun_facts)

    (out_dir / "candidates.json").write_text(json.dumps(candidates_view, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "selected.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "brief.html").write_text(html_doc, encoding="utf-8")
    (out_dir / "brief.txt").write_text(text_doc, encoding="utf-8")

    subject = args.subject or f"金融 AI 资讯简报 | {args.date}"
    recipients = parse_recipients(args.recipient)

    if args.send_email:
        send_email(subject, html_doc, text_doc, recipients)
        print(json.dumps({
            "ok": True,
            "message": "brief generated and emailed",
            "output_dir": str(out_dir.resolve()),
            "recipients": recipients,
            "subject": subject,
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            "ok": True,
            "message": "brief generated",
            "output_dir": str(out_dir.resolve()),
            "recipients": recipients,
            "subject": subject,
        }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
