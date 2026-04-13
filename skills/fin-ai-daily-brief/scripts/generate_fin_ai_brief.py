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
import subprocess
import sys
from email.mime.multipart import MIMEMultipart
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
TAVILY_SEARCH_SCRIPT = REPO_ROOT / "skills" / "tavily-search" / "scripts" / "tavily_search.py"

DEFAULT_QUERY = "金融 AI"
DEFAULT_TOPIC = "news"
DEFAULT_TOP_K = 20
DEFAULT_KEEP = 10
DEFAULT_CANDIDATE_LIMIT = 15
DEFAULT_COUNTRY = "china"
DEFAULT_INCLUDE_DOMAINS = [
    "36kr.com",
    "wallstreetcn.com",
    "cls.cn",
    "stcn.com",
    "yicai.com",
    "jrj.com.cn",
    "eastmoney.com",
    "cs.com.cn",
    "caixin.com",
    "cnstock.com",
    "finance.sina.com.cn",
    "news.cn",
]
DEFAULT_EXCLUDE_DOMAINS = [
    "marketbeat.com",
    "insidermonkey.com",
    "gurufocus.com",
    "cbsnews.com",
    "hospitalitynet.org",
    "developingtelecoms.com",
    "chainstoreage.com",
]
DEFAULT_QUERY_VARIANTS = [
    "中文 金融 AI 应用 银行 券商 保险 资管 大模型 智能投研 风控 合规",
    "中文 银行 AI 券商 AI 保险 AI 资管 AI 金融科技",
    "中文 证券 券商 投研 AI 智能投顾 金融大模型",
    "中文 保险 AI 风控 合规 智能客服 金融科技",
    "中文 金融监管 AI 银行业大模型 券商大模型 投研智能体",
    "中文 银行 大模型 客服 风控 智能运营",
    "中文 券商 AI 研究 投顾 合规 风控",
    "中文 资管 基金 AI 投研 风险管理",
]
RECENT_QUERY_SUFFIXES = [
    "最近7天",
    "近7日",
    "本周",
]
MIN_SELECTED_ITEMS = 3
MIN_SCORE_TO_KEEP = 18
NOISY_HOSTS = {
    "marketbeat.com",
    "insidermonkey.com",
    "gurufocus.com",
    "cbsnews.com",
    "hospitalitynet.org",
    "developingtelecoms.com",
    "chainstoreage.com",
}

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
    "household": -8,
    "at home": -8,
    "home helper": -8,
    "grocery": -6,
    "travel": -5,
    "pizza": -6,
    "consumer": -3,
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
    "36kr.com": 6,
    "cls.cn": 7,
    "wallstreetcn.com": 6,
    "stcn.com": 6,
    "yicai.com": 6,
    "caixin.com": 7,
    "jrj.com.cn": 5,
    "eastmoney.com": 5,
    "21jingji.com": 6,
    "cs.com.cn": 6,
    "cnstock.com": 6,
    "sina.com.cn": 4,
    "sohu.com": 3,
    "163.com": 3,
}

FUN_FACTS = [
    "今天的 AI 趣味知识：Transformer 最早在 2017 年被系统提出，它最核心的突破之一，是让模型能同时关注一句话里的多个位置。",
    "大模型并不是像人一样‘理解’世界，它更像是在超大规模语料上学会了高维概率接龙，但这种接龙已经足够强到能辅助很多金融知识工作。",
    "对金融行业来说，真正有价值的 AI 往往不是最会聊天的模型，而是最能稳定接入数据、流程、权限和审计体系的那一个。",
    "很多金融 AI 应用的瓶颈并不在模型本身，而在数据治理、权限边界、可追溯性和人工复核机制。",
    "Agent 的关键不只是会调用工具，而是能在复杂流程里持续保持目标、上下文和风险约束。",
    "检索增强生成（RAG）之所以对金融场景重要，是因为它能把‘模型记忆’和‘机构最新知识库’结合起来。",
]


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


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def hostname_from_url(url: str) -> str:
    match = re.match(r"https?://([^/]+)", url or "")
    return (match.group(1).lower() if match else "").replace("www.", "")


def canonicalize_url(url: str) -> str:
    raw = normalize_text(url)
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except Exception:
        return raw
    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    kept = []
    for key, value in parse_qsl(parts.query, keep_blank_values=False):
        if key.lower().startswith(("utm_", "spm", "from", "feature", "ref", "mod", "loc", "r", "rfunc", "tj", "tr", "cre")):
            continue
        kept.append((key, value))
    query = urlencode(kept)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def looks_like_low_value_page(item: dict) -> bool:
    title = normalize_text(item.get("title") or "").lower()
    summary = normalize_text(item.get("summary") or item.get("content") or "").lower()
    url = canonicalize_url(item.get("url") or "")
    host = hostname_from_url(url)
    path = urlsplit(url).path.lower() if url else ""
    text = f"{title} {summary} {host} {path}"

    blocked_terms = [
        "财经门户", "门户", "首页", "index.html", "查看pdf原文", "招募说明书", "基金更新", "基金管理人", "基金托管人", "公告", "pdf原文", "产品经理", "营收", "财报", "股吧", "博客"
    ]
    if any(term.lower() in text for term in blocked_terms):
        return True
    if path in {"", "/", "/index.html", "/index.htm"}:
        return True
    if "gonggao" in path or "fund" in host:
        return True
    return False


def summarize_item(item: dict) -> str:
    content = normalize_text(item.get("summary") or item.get("content") or item.get("raw_content") or "")
    if not content:
        return normalize_text(item.get("title") or "")[:120]
    if len(content) > 140:
        return content[:137].rstrip() + "..."
    return content


def split_recipients(raw: str) -> List[str]:
    return [part.strip() for part in re.split(r"[,;\n]+", raw or "") if part.strip()]


def dedupe_items(items: List[dict]) -> List[dict]:
    seen = set()
    output = []
    for item in items:
        url = canonicalize_url(item.get("url") or "")
        title = normalize_text(item.get("title") or "")
        key = url.lower() or title.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        cloned = dict(item)
        if url:
            cloned["url"] = url
        output.append(cloned)
    return output


def normalize_result_item(item: dict) -> Optional[dict]:
    if not isinstance(item, dict):
        return None
    item_type = normalize_text(str(item.get("type") or item.get("result_type") or "")).lower()
    if item.get("is_sponsored") or item.get("sponsored"):
        return None
    if item_type in {"ad", "ads", "sponsored", "ai_overview", "overview"}:
        return None

    title = normalize_text(item.get("zh_title") or item.get("title") or item.get("headline") or "")
    url = canonicalize_url(item.get("url") or item.get("link") or "")
    if not title or not url:
        return None
    if "/aclk?" in url or url.startswith("https://www.google.com/"):
        return None

    summary = normalize_text(item.get("zh_summary") or item.get("summary") or item.get("snippet") or item.get("content") or item.get("raw_content") or "")
    candidate = {
        "title": title,
        "url": url,
        "summary": summary,
        "content": summary,
        "published_date": normalize_text(item.get("published_date") or item.get("date") or ""),
        "source": normalize_text(item.get("source") or hostname_from_url(url) or "unknown"),
    }
    if looks_like_low_value_page(candidate):
        return None
    return candidate


def load_input_results(path: Path, limit: int = DEFAULT_CANDIDATE_LIMIT) -> List[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results", []) if isinstance(payload, dict) else payload
    output = []
    for item in results:
        normalized = normalize_result_item(item)
        if not normalized:
            continue
        output.append(normalized)
        if len(output) >= limit:
            break
    return output


def load_search_results(input_results: str, query: str, topic: str, candidate_limit: int = DEFAULT_CANDIDATE_LIMIT) -> tuple[list[dict], dict]:
    if input_results:
        input_path = Path(input_results)
        raw_items = load_input_results(input_path, limit=candidate_limit)
        search_result = {
            "ok": True,
            "query": query,
            "topic": topic,
            "source": "input-results",
            "input_results": str(input_path.resolve()),
            "response": {"results": raw_items},
        }
        return raw_items, search_result

    search_result = multi_search(
        primary_query=query,
        topic=topic,
        target_count=max(candidate_limit, DEFAULT_TOP_K),
        country=DEFAULT_COUNTRY,
        include_domains=DEFAULT_INCLUDE_DOMAINS,
        exclude_domains=DEFAULT_EXCLUDE_DOMAINS,
    )
    if not search_result.get("ok"):
        raise RuntimeError(f"tavily-search failed: {json.dumps(search_result, ensure_ascii=False)}")
    raw_items = []
    for item in search_result.get("response", {}).get("results", []):
        normalized = normalize_result_item(item) or normalize_result_item({
            "title": item.get("title"),
            "url": item.get("url"),
            "summary": item.get("content") or item.get("raw_content") or item.get("summary") or "",
            "published_date": item.get("published_date") or item.get("date") or "",
            "source": item.get("source") or hostname_from_url(item.get("url") or ""),
        })
        if normalized:
            raw_items.append(normalized)
    return raw_items[:candidate_limit], search_result


def load_google_results(input_results: str, candidate_limit: int = DEFAULT_CANDIDATE_LIMIT) -> tuple[list[dict], dict]:
    return load_search_results(input_results=input_results, query=DEFAULT_QUERY, topic=DEFAULT_TOPIC, candidate_limit=candidate_limit)


def tavily_search(query: str, topic: str, max_results: int, country: str = "", include_domains: Optional[List[str]] = None, exclude_domains: Optional[List[str]] = None, days: int = 7) -> dict:
    if not TAVILY_SEARCH_SCRIPT.exists():
        raise RuntimeError(f"tavily-search script not found: {TAVILY_SEARCH_SCRIPT}")

    cmd = [
        "python3",
        str(TAVILY_SEARCH_SCRIPT),
        query,
        "--topic", topic,
        "--max-results", str(max_results),
        "--search-depth", "advanced",
        "--include-answer",
        "--include-domains", ",".join(include_domains or []),
        "--exclude-domains", ",".join(exclude_domains or []),
    ]
    if topic == "news":
        cmd += ["--days", str(days)]

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), env=os.environ.copy())
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if not stdout:
        raise RuntimeError(f"tavily-search returned empty output: {stderr}")

    try:
        result = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"failed to parse tavily-search output: {exc}; stderr={stderr}; stdout={stdout[:500]}") from exc

    if country and topic == "general":
        result["country"] = country
    if include_domains:
        result["include_domains"] = include_domains
    if exclude_domains:
        result["exclude_domains"] = exclude_domains
    if topic == "news":
        result["days"] = days
    return result


def build_query_variants(primary_query: str, topic: str) -> List[str]:
    queries = [primary_query] + [q for q in DEFAULT_QUERY_VARIANTS if q != primary_query]
    if topic == "news":
        extra = []
        for query in queries:
            for suffix in RECENT_QUERY_SUFFIXES:
                candidate = f"{query} {suffix}".strip()
                if candidate not in queries and candidate not in extra:
                    extra.append(candidate)
        queries.extend(extra)
    return queries


def build_search_plans(primary_query: str, requested_topic: str, include_domains: Optional[List[str]], exclude_domains: Optional[List[str]], recent_days: int = 7) -> List[dict]:
    plans = []

    def add_plan(topic: str, include: Optional[List[str]], label: str) -> None:
        plan = {
            "topic": topic,
            "include_domains": include or [],
            "exclude_domains": exclude_domains or [],
            "days": recent_days if topic == "news" else 0,
            "label": label,
            "queries": build_query_variants(primary_query, topic),
        }
        key = (plan["topic"], tuple(plan["include_domains"]), tuple(plan["exclude_domains"]), plan["days"])
        existing_keys = {
            (p["topic"], tuple(p["include_domains"]), tuple(p["exclude_domains"]), p["days"])
            for p in plans
        }
        if key not in existing_keys:
            plans.append(plan)

    add_plan(requested_topic, include_domains, "requested-strict")
    if requested_topic != "news":
        add_plan("news", include_domains, "recent-news-strict")
    add_plan("news", [], "recent-news-broad")
    if requested_topic != "general":
        add_plan("general", include_domains, "general-strict")
    add_plan("general", [], "general-broad")
    return plans


def multi_search(primary_query: str, topic: str, target_count: int, country: str = "", include_domains: Optional[List[str]] = None, exclude_domains: Optional[List[str]] = None) -> dict:
    all_results = []
    search_runs = []
    per_query = max(6, min(10, target_count))
    plans = build_search_plans(primary_query, topic, include_domains, exclude_domains, recent_days=7)

    for plan in plans:
        for query in plan["queries"]:
            result = tavily_search(
                query,
                plan["topic"],
                per_query,
                country=country,
                include_domains=plan["include_domains"],
                exclude_domains=plan["exclude_domains"],
                days=plan["days"] or 7,
            )
            result["plan_label"] = plan["label"]
            search_runs.append(result)
            if result.get("ok"):
                for item in result.get("response", {}).get("results", []):
                    normalized = normalize_result_item(item) or normalize_result_item({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "summary": item.get("content") or item.get("raw_content") or "",
                        "published_date": item.get("published_date") or "",
                        "source": hostname_from_url(item.get("url") or ""),
                    })
                    if normalized:
                        all_results.append(normalized)
            if len(dedupe_items(all_results)) >= target_count * 2:
                break
        if len(dedupe_items(all_results)) >= target_count * 2:
            break

    merged = dedupe_items(all_results)
    ok = any(run.get("ok") for run in search_runs)
    return {
        "ok": ok,
        "query": primary_query,
        "topic": topic,
        "country": country,
        "include_domains": include_domains or [],
        "exclude_domains": exclude_domains or [],
        "search_runs": search_runs,
        "response": {"results": merged} if ok else {},
    }


def score_item(item: dict) -> int:
    title_text = normalize_text(item.get("title") or "").lower()
    content_text = normalize_text(item.get("summary") or item.get("content") or item.get("raw_content") or "").lower()
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
    if contains_chinese(title) or contains_chinese(content_text):
        score += 12
    if len(title) >= 18:
        score += 1
    if item.get("published_date"):
        score += 1
    return score


def is_relevant_fin_ai_item(item: dict) -> bool:
    title = normalize_text(item.get("title") or "")
    content = normalize_text(item.get("summary") or item.get("content") or item.get("raw_content") or "")
    text = f"{title} {content}".lower()
    host = hostname_from_url(item.get("url") or "")

    finance_terms = [
        "银行", "券商", "证券", "保险", "资管", "基金", "金融", "fintech", "financial", "bank", "banking", "asset management", "wealth", "broker", "trading", "investment", "payments", "payment", "lending", "underwriting", "claims", "fraud"
    ]
    ai_terms = [
        "ai", "agent", "智能体", "llm", "大模型", "人工智能", "模型", "机器学习", "automation", "copilot", "生成式", "genai"
    ]
    noise_terms = [
        "sports", "retail associate", "shopping assistant", "apartment portfolio", "movie", "game", "fashion", "at home", "home helper", "order pizza", "travel booking"
    ]
    business_terms = [
        "underwriting", "claims", "fraud", "risk", "compliance", "governance", "loan", "lending", "wealth", "portfolio", "payments", "customer service", "投研", "风控", "合规", "承保", "理赔", "贷款", "支付", "财富管理", "投顾", "客服"
    ]

    finance_hits = sum(1 for term in finance_terms if term.lower() in text)
    ai_hits = sum(1 for term in ai_terms if term.lower() in text)
    noise_hits = sum(1 for term in noise_terms if term in text)
    business_hits = sum(1 for term in business_terms if term.lower() in text)
    has_cn = contains_chinese(title) or contains_chinese(content)
    high_signal = business_hits >= 2
    score = score_item(item)

    if host in NOISY_HOSTS:
        return False
    if noise_hits > 0:
        return False
    if len(title) < 8:
        return False
    if finance_hits < 1 or ai_hits < 1:
        return False
    if business_hits < 1 and score < MIN_SCORE_TO_KEEP + 10:
        return False
    if len(content) < 30 and len(title) < 18:
        return False
    if score < MIN_SCORE_TO_KEEP:
        return False
    if has_cn:
        return high_signal or score >= MIN_SCORE_TO_KEEP + 4
    return high_signal or score >= MIN_SCORE_TO_KEEP + 12


def build_candidate_items(items: List[dict], limit: int = DEFAULT_CANDIDATE_LIMIT) -> List[dict]:
    enriched = []
    for item in items:
        if looks_like_low_value_page(item):
            continue
        enriched.append({
            "title": normalize_text(item.get("title") or "未命名资讯"),
            "summary": normalize_text(item.get("summary") or summarize_item(item)),
            "url": canonicalize_url(item.get("url") or ""),
            "source": normalize_text(item.get("source") or hostname_from_url(item.get("url") or "") or "unknown"),
            "published_date": item.get("published_date") or "",
            "score": score_item(item),
        })
    enriched.sort(key=lambda x: (x["score"], x["published_date"]), reverse=True)
    return enriched[:limit]


def select_top_items(items: List[dict], keep: int) -> List[dict]:
    enriched = build_candidate_items(items, limit=len(items))
    enriched.sort(key=lambda x: (x["score"], x["published_date"]), reverse=True)
    return enriched[:keep]


def build_overview(selected: List[dict], date_str: str, query: str) -> str:
    focus_terms = []
    for item in selected:
        text = (item["title"] + " " + item["summary"]).lower()
        for term in ["银行", "券商", "保险", "资管", "风控", "合规", "投研", "agent", "智能体", "大模型", "监管"]:
            if term.lower() in text and term not in focus_terms:
                focus_terms.append(term)
    top_focus = "、".join(focus_terms[:5]) if focus_terms else "金融机构 AI 落地"
    if not selected:
        return f"{date_str} 的金融 AI 简报今天没有发现足够值得纳入的高信号资讯。当前更值得持续跟踪的方向，仍然是 {top_focus}、监管要求映射，以及分析与运营效率提升相关的实际应用。搜索主题为：{query}。"
    return f"{date_str} 的金融 AI 简报聚焦 {top_focus} 等方向。整体看，真正值得金融机构关注的，不是泛 AI 热点，而是能映射到业务流程、监管要求和分析效率提升的实际应用。搜索主题为：{query}。"


def choose_fun_facts() -> List[str]:
    return random.sample(FUN_FACTS, k=3) if len(FUN_FACTS) >= 3 else FUN_FACTS


def build_html(date_str: str, overview: str, items: List[dict], fun_facts: List[str], candidate_items: Optional[List[dict]] = None, search_query: str = "") -> str:
    selected_cards = []
    for idx, item in enumerate(items, start=1):
        selected_cards.append(f"""
        <section class=\"card selected\">
          <div class=\"meta\">精选 #{idx} · {html.escape(item['source'])}</div>
          <h3><a href=\"{html.escape(item['url'])}\" target=\"_blank\">{html.escape(item['title'])}</a></h3>
          <p>{html.escape(item['summary'])}</p>
          <div class=\"chip-row\"><span class=\"chip\">价值分 {item['score']}</span></div>
          <div class=\"link\"><a href=\"{html.escape(item['url'])}\" target=\"_blank\">查看原文</a></div>
        </section>
        """)

    candidate_cards = []
    for idx, item in enumerate(candidate_items or [], start=1):
        candidate_cards.append(f"""
        <section class=\"card candidate\">
          <div class=\"meta\">Tavily #{idx} · {html.escape(item['source'])}</div>
          <h3><a href=\"{html.escape(item['url'])}\" target=\"_blank\">{html.escape(item['title'])}</a></h3>
          <p>{html.escape(item['summary'])}</p>
          <div class=\"link\"><a href=\"{html.escape(item['url'])}\" target=\"_blank\">查看原文</a></div>
        </section>
        """)

    facts_html = "".join(f"<li>{html.escape(fact)}</li>" for fact in fun_facts)
    query_badge = f'<div class="query-badge">搜索词：{html.escape(search_query)}</div>' if search_query else ""

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
      --hero1: #0f172a;
      --hero2: #1d4ed8;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: var(--bg); color: var(--text); }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 48px; }}
    .hero {{ background: linear-gradient(135deg, var(--hero1), var(--hero2)); color: white; border-radius: 22px; padding: 28px; margin-bottom: 24px; }}
    .hero h1 {{ margin: 0 0 10px; font-size: 34px; }}
    .hero p {{ margin: 0; line-height: 1.75; color: rgba(255,255,255,0.93); }}
    .query-badge {{ display: inline-flex; margin-top: 14px; padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,0.14); font-size: 13px; }}
    .section-title {{ font-size: 22px; margin: 28px 0 14px; }}
    .section-note {{ margin: -6px 0 16px; color: var(--muted); font-size: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 18px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    .candidate {{ background: #f8fafc; }}
    .selected {{ background: #ffffff; border-color: #dbeafe; }}
    .card h3 {{ margin: 8px 0 10px; font-size: 19px; line-height: 1.45; }}
    .card p {{ margin: 0; line-height: 1.7; color: #374151; }}
    .meta {{ font-size: 13px; color: var(--muted); }}
    .chip-row {{ margin-top: 12px; }}
    .chip {{ display: inline-flex; padding: 4px 10px; border-radius: 999px; background: #eff6ff; color: #1d4ed8; font-size: 12px; }}
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
      {query_badge}
    </div>

    <h2 class=\"section-title\">Tavily 搜索前 15 条结果</h2>
    <div class=\"section-note\">按 Tavily 搜索结果保留前 15 条候选，并过滤广告/低价值页面。</div>
    <div class=\"grid\">{''.join(candidate_cards)}</div>

    <h2 class=\"section-title\">精选 10 条高价值资讯</h2>
    <div class=\"section-note\">从前 15 条候选里筛选出对金融企业更有价值的内容。</div>
    <div class=\"grid\">{''.join(selected_cards)}</div>

    <h2 class=\"section-title\">今日 AI 趣味知识</h2>
    <section class=\"card fun\"><ul>{facts_html}</ul></section>

    <div class=\"footer\">本简报由 fin-ai-daily-brief 自动生成，可继续扩展订阅用户列表。</div>
  </div>
</body>
</html>
"""


def build_text(date_str: str, overview: str, items: List[dict], fun_facts: List[str], candidate_items: Optional[List[dict]] = None, search_query: str = "") -> str:
    lines = [f"金融 AI 资讯简报 - {date_str}", ""]
    if search_query:
        lines.extend([f"搜索词：{search_query}", ""])
    lines.extend(["总览：", overview, "", "Tavily 搜索前 15 条结果："])
    for idx, item in enumerate(candidate_items or [], start=1):
        lines.extend([
            f"{idx}. {item['title']}",
            f"   简述：{item['summary']}",
            f"   链接：{item['url']}",
            "",
        ])
    lines.append("精选 10 条高价值资讯：")
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
    emails: List[str] = []
    subscriber_file = os.environ.get("FIN_AI_SUBSCRIBERS_FILE", "").strip()
    if subscriber_file:
        file_path = Path(subscriber_file)
        if file_path.exists():
            emails.extend(split_recipients(file_path.read_text(encoding="utf-8")))
    emails.extend(split_recipients(os.environ.get("FIN_AI_SUBSCRIBERS", "")))
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
        raise RuntimeError("No recipients configured. Set FIN_AI_SUBSCRIBERS / FIN_AI_SUBSCRIBERS_FILE or use --recipient")

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
    parser.add_argument("--topic", default=DEFAULT_TOPIC, choices=["general", "news", "finance"])
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    parser.add_argument("--country", default=DEFAULT_COUNTRY)
    parser.add_argument("--include-domain", action="append", default=[])
    parser.add_argument("--exclude-domain", action="append", default=[])
    parser.add_argument("--output-dir", default="./output")
    parser.add_argument("--input-results", default="", help="Optional pre-collected results JSON; omit to search via tavily-search")
    parser.add_argument("--candidate-limit", type=int, default=DEFAULT_CANDIDATE_LIMIT)
    parser.add_argument("--recipient", action="append", default=[])
    parser.add_argument("--subscribers-file", default="")
    parser.add_argument("--send-email", action="store_true")
    parser.add_argument("--subject", default="")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.subscribers_file:
        os.environ["FIN_AI_SUBSCRIBERS_FILE"] = args.subscribers_file

    raw_items, search_result = load_search_results(args.input_results, args.query, args.topic, candidate_limit=args.candidate_limit)

    (out_dir / "search-result.json").write_text(json.dumps(search_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    deduped = dedupe_items(raw_items)
    candidate_items = build_candidate_items(deduped, limit=args.candidate_limit)
    filtered = [item for item in deduped if is_relevant_fin_ai_item(item)]
    if len(filtered) < args.keep:
        fallback_pool = [item for item in deduped if not looks_like_low_value_page(item)]
        filtered = fallback_pool or deduped
    selected = select_top_items(filtered, args.keep)

    overview = build_overview(selected, args.date, args.query)
    fun_facts = choose_fun_facts()
    html_doc = build_html(args.date, overview, selected, fun_facts, candidate_items=candidate_items, search_query=args.query)
    text_doc = build_text(args.date, overview, selected, fun_facts, candidate_items=candidate_items, search_query=args.query)

    (out_dir / "candidates.json").write_text(json.dumps(candidate_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
