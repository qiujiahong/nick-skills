#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
TAVILY_SKILL_DIR = REPO_ROOT / "skills" / "tavily-search"
TAVILY_SEARCH_SCRIPT = TAVILY_SKILL_DIR / "scripts" / "tavily_search.py"

DEFAULT_DAYS = 30
DEFAULT_MAX_PER_SECTION = 3
DEFAULT_QUERIES_PER_SECTION = 2
DEFAULT_SEARCH_DEPTH = "advanced"
SECTION_ORDER = ["official", "latest", "tutorials", "open_source", "comparisons"]
SECTION_LABELS = {
    "official": "官方文档与权威资料",
    "latest": "最新动态",
    "tutorials": "教程与实战",
    "open_source": "开源项目",
    "comparisons": "对比与观点",
}
DEFAULT_EXCLUDE_DOMAINS = [
    "pinterest.com",
    "reddit.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
]
CANONICAL_DROP_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "ref_src",
    "fbclid",
    "gclid",
}

TOPIC_PROFILES = {
    "protocol": {
        "keywords": ["mcp", "a2a", "protocol", "spec", "agent2agent", "model context protocol"],
        "summary": "协议 / 标准",
        "sections": {
            "official": ["{topic} official documentation", "{topic} specification", "{topic} official blog"],
            "latest": ["{topic} latest updates", "{topic} release notes", "{topic} news"],
            "tutorials": ["{topic} tutorial", "{topic} example", "{topic} architecture"],
            "open_source": ["{topic} GitHub", "{topic} SDK", "{topic} reference implementation"],
            "comparisons": ["{topic} vs function calling", "{topic} vs api", "{topic} comparison"],
        },
    },
    "model_api": {
        "keywords": ["api", "sdk", "responses", "realtime", "function calling", "tool calling", "model", "embedding"],
        "summary": "模型 / API",
        "sections": {
            "official": ["{topic} official documentation", "{topic} API docs", "{topic} official guide"],
            "latest": ["{topic} latest updates", "{topic} changelog", "{topic} announcement"],
            "tutorials": ["{topic} tutorial", "{topic} code example", "{topic} best practices"],
            "open_source": ["{topic} GitHub example", "{topic} starter", "{topic} sample app"],
            "comparisons": ["{topic} vs assistants api", "{topic} vs chat completions", "{topic} comparison"],
        },
    },
    "framework": {
        "keywords": ["langgraph", "autogen", "crewai", "mastra", "openhands", "framework", "orchestration"],
        "summary": "开源框架 / 编排",
        "sections": {
            "official": ["{topic} official docs", "{topic} official blog", "{topic} architecture"],
            "latest": ["{topic} latest updates", "{topic} release notes", "{topic} news"],
            "tutorials": ["{topic} tutorial", "{topic} production example", "{topic} best practices"],
            "open_source": ["{topic} GitHub", "{topic} examples", "{topic} template"],
            "comparisons": ["{topic} vs langchain", "{topic} vs autogen", "{topic} comparison"],
        },
    },
    "engineering": {
        "keywords": ["rag", "eval", "evaluation", "memory", "agent memory", "observability", "workflow", "retrieval"],
        "summary": "工程实践",
        "sections": {
            "official": ["{topic} official documentation", "{topic} guide", "{topic} architecture"],
            "latest": ["{topic} latest research", "{topic} latest updates", "{topic} news"],
            "tutorials": ["{topic} tutorial", "{topic} production guide", "{topic} implementation"],
            "open_source": ["{topic} GitHub", "{topic} toolkit", "{topic} starter"],
            "comparisons": ["{topic} vs fine tuning", "{topic} vs long context", "{topic} tradeoffs"],
        },
    },
    "general_ai": {
        "keywords": [],
        "summary": "通用 AI 技术主题",
        "sections": {
            "official": ["{topic} official documentation", "{topic} official blog", "{topic} guide"],
            "latest": ["{topic} latest updates", "{topic} news", "{topic} release notes"],
            "tutorials": ["{topic} tutorial", "{topic} practical guide", "{topic} example"],
            "open_source": ["{topic} GitHub", "{topic} open source", "{topic} examples"],
            "comparisons": ["{topic} comparison", "{topic} vs alternatives", "{topic} best practices"],
        },
    },
}
TOPIC_ALIASES = {
    "mcp": {
        "search_topic": "Model Context Protocol MCP",
        "intent_terms": ["model context protocol", "mcp", "agent", "tool", "server"],
    },
    "a2a": {
        "search_topic": "Agent2Agent A2A protocol",
        "intent_terms": ["agent2agent", "a2a", "agent", "protocol"],
    },
    "responses api": {
        "search_topic": "OpenAI Responses API",
        "intent_terms": ["responses api", "openai", "response", "tool", "reasoning"],
    },
    "ai coding agent": {
        "search_topic": "AI coding agent",
        "intent_terms": ["coding agent", "agent", "code", "developer", "repository"],
    },
    "rag": {
        "search_topic": "retrieval augmented generation RAG",
        "intent_terms": ["retrieval augmented generation", "rag", "retrieval", "vector", "knowledge base"],
    },
}

OFFICIAL_DOMAINS = {
    "openai.com": 14,
    "platform.openai.com": 16,
    "docs.anthropic.com": 15,
    "anthropic.com": 12,
    "modelcontextprotocol.io": 18,
    "github.com": 8,
    "docs.github.com": 10,
    "cloud.google.com": 10,
    "ai.google.dev": 12,
    "learn.microsoft.com": 11,
    "microsoft.com": 9,
    "docs.langchain.com": 11,
    "langchain.com": 9,
    "langchain-ai.github.io": 10,
    "langgraph.dev": 12,
}
QUALITY_DOMAINS = {
    "arxiv.org": 8,
    "huggingface.co": 8,
    "techcrunch.com": 3,
    "theverge.com": 3,
    "infoq.com": 7,
    "medium.com": 2,
    "substack.com": 3,
    "simonwillison.net": 8,
    "latent.space": 6,
    "martinfowler.com": 6,
}


@dataclass
class SearchHit:
    section: str
    query: str
    title: str
    url: str
    content: str
    domain: str
    score: int
    raw: dict


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
    for base_dir in (SKILL_DIR, TAVILY_SKILL_DIR):
        for name in (".env.local", ".env"):
            load_env_file(base_dir / name)


def detect_profile(topic: str) -> str:
    normalized = topic.lower()
    for profile_name, profile in TOPIC_PROFILES.items():
        for keyword in profile["keywords"]:
            if keyword in normalized:
                return profile_name
    return "general_ai"


def resolve_topic_alias(topic: str) -> Tuple[str, List[str]]:
    normalized = normalize_text(topic).lower()
    alias = TOPIC_ALIASES.get(normalized)
    if alias:
        return alias["search_topic"], alias["intent_terms"]
    return topic, [normalized]


def split_csv(value: str) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def hostname_from_url(url: str) -> str:
    match = re.match(r"https?://([^/]+)", url or "")
    if not match:
        return ""
    return match.group(1).lower().removeprefix("www.")


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in CANONICAL_DROP_QUERY_KEYS
    ]
    canonical = urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(filtered_query, doseq=True),
            "",
        )
    )
    return canonical.rstrip("/")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def trim_text(value: str, limit: int = 180) -> str:
    text = normalize_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def source_bonus(domain: str) -> int:
    for name, weight in OFFICIAL_DOMAINS.items():
        if domain == name or domain.endswith("." + name):
            return weight
    for name, weight in QUALITY_DOMAINS.items():
        if domain == name or domain.endswith("." + name):
            return weight
    return 0


def keyword_score(topic: str, query: str, title: str, content: str) -> int:
    topic_tokens = [token for token in re.split(r"[^a-zA-Z0-9\u4e00-\u9fff]+", topic.lower()) if token]
    query_tokens = [token for token in re.split(r"[^a-zA-Z0-9\u4e00-\u9fff]+", query.lower()) if token]
    haystack = f"{title} {content}".lower()
    score = 0
    for token in topic_tokens:
        if token in haystack:
            score += 6
    for token in query_tokens:
        if token in haystack:
            score += 2
    return score


def score_hit(
    search_topic: str,
    query: str,
    section: str,
    title: str,
    content: str,
    domain: str,
    url: str,
    intent_terms: Sequence[str],
) -> int:
    score = keyword_score(search_topic, query, title, content)
    score += source_bonus(domain)
    lowered = f"{title} {content} {url}".lower()

    if section == "official":
        if any(keyword in lowered for keyword in ["official", "documentation", "docs", "guide", "spec", "reference"]):
            score += 8
    if section == "latest":
        if any(keyword in lowered for keyword in ["latest", "release", "launch", "announcement", "news", "update", "changelog"]):
            score += 7
    if section == "tutorials":
        if any(keyword in lowered for keyword in ["tutorial", "example", "how to", "guide", "walkthrough", "best practices"]):
            score += 7
    if section == "open_source":
        if "github.com" in domain or any(keyword in lowered for keyword in ["open source", "repository", "repo", "sdk"]):
            score += 8
    if section == "comparisons":
        if any(keyword in lowered for keyword in [" vs ", "comparison", "tradeoff", "alternatives", "benchmark"]):
            score += 8

    matched_intent_terms = sum(1 for term in intent_terms if term and term.lower() in lowered)
    score += matched_intent_terms * 5
    if matched_intent_terms == 0:
        score -= 12

    if any(noisy in domain for noisy in DEFAULT_EXCLUDE_DOMAINS):
        score -= 8
    return score


def build_queries(search_topic: str, profile_name: str) -> Dict[str, List[str]]:
    profile = TOPIC_PROFILES[profile_name]
    return {
        section: [template.format(topic=search_topic) for template in templates]
        for section, templates in profile["sections"].items()
    }


def run_tavily_search(
    query: str,
    topic_kind: str,
    search_depth: str,
    days: int,
    max_results: int,
    include_domains: Sequence[str],
    exclude_domains: Sequence[str],
) -> dict:
    if not TAVILY_SEARCH_SCRIPT.exists():
        raise RuntimeError(f"missing tavily-search script: {TAVILY_SEARCH_SCRIPT}")

    cmd = [
        "python3",
        str(TAVILY_SEARCH_SCRIPT),
        query,
        "--topic",
        topic_kind,
        "--search-depth",
        search_depth,
        "--max-results",
        str(max_results),
        "--include-answer",
    ]
    if topic_kind == "news":
        cmd.extend(["--days", str(days)])
    if include_domains:
        cmd.extend(["--include-domains", ",".join(include_domains)])
    if exclude_domains:
        cmd.extend(["--exclude-domains", ",".join(exclude_domains)])

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=os.environ.copy(),
    )
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if not stdout:
        raise RuntimeError(f"tavily-search returned empty output: {stderr}")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"failed to parse tavily-search output: {exc}; stderr={stderr}; stdout={stdout[:300]}"
        ) from exc


def collect_hits(
    search_topic: str,
    queries_by_section: Dict[str, List[str]],
    search_depth: str,
    days: int,
    queries_per_section: int,
    include_domains: Sequence[str],
    exclude_domains: Sequence[str],
    intent_terms: Sequence[str],
) -> Tuple[List[SearchHit], List[dict]]:
    hits: List[SearchHit] = []
    search_runs: List[dict] = []

    for section in SECTION_ORDER:
        for query in queries_by_section.get(section, [])[: max(1, queries_per_section)]:
            topic_kind = "news" if section == "latest" else "general"
            result = run_tavily_search(
                query=query,
                topic_kind=topic_kind,
                search_depth=search_depth,
                days=days,
                max_results=5,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
            )
            search_runs.append({"section": section, "query": query, "result": result})
            if not result.get("ok"):
                continue

            for item in result.get("response", {}).get("results", []):
                title = normalize_text(item.get("title") or "")
                url = normalize_text(item.get("url") or "")
                content = trim_text(item.get("content") or item.get("raw_content") or "")
                domain = hostname_from_url(url)
                if not title or not url:
                    continue
                score = score_hit(search_topic, query, section, title, content, domain, url, intent_terms)
                hits.append(
                    SearchHit(
                        section=section,
                        query=query,
                        title=title,
                        url=url,
                        content=content,
                        domain=domain,
                        score=score,
                        raw=item,
                    )
                )
    return hits, search_runs


def dedupe_and_rank(hits: Sequence[SearchHit], max_per_section: int) -> Dict[str, List[SearchHit]]:
    seen_urls = set()
    grouped: Dict[str, List[SearchHit]] = {section: [] for section in SECTION_ORDER}
    ordered_hits = sorted(
        hits,
        key=lambda hit: (SECTION_ORDER.index(hit.section), -hit.score, hit.domain, hit.title),
    )

    for hit in ordered_hits:
        canonical_url = canonicalize_url(hit.url)
        if canonical_url in seen_urls:
            continue
        if len(grouped[hit.section]) >= max_per_section:
            continue
        grouped[hit.section].append(hit)
        seen_urls.add(canonical_url)
    return grouped


def build_takeaways(topic: str, profile_name: str, grouped_hits: Dict[str, List[SearchHit]]) -> List[str]:
    takeaways = []
    official = grouped_hits.get("official", [])
    latest = grouped_hits.get("latest", [])
    open_source = grouped_hits.get("open_source", [])
    tutorials = grouped_hits.get("tutorials", [])

    if official:
        takeaways.append(f"`{topic}` 更适合先从官方资料切入，优先看 {official[0].domain}。")
    if latest:
        takeaways.append(f"这个主题最近仍在快速演进，建议先看最新动态，再决定是否投入学习。")
    if open_source:
        takeaways.append(f"开源生态已经有可直接上手的项目，适合边看文档边跑示例。")
    if tutorials:
        takeaways.append(f"社区教程已经比较丰富，适合把官方概念和实战经验对照着看。")
    if not takeaways:
        takeaways.append(f"`{topic}` 的高质量公开资料不算多，建议缩小主题或增加限定词后再搜。")

    takeaways.append(f"主题类型判断：{TOPIC_PROFILES[profile_name]['summary']}。")
    return takeaways[:4]


def render_markdown(
    topic: str,
    profile_name: str,
    grouped_hits: Dict[str, List[SearchHit]],
    takeaways: Sequence[str],
    view: str,
) -> str:
    lines = [
        f"# {topic}",
        "",
        f"- 主题类型：{TOPIC_PROFILES[profile_name]['summary']}",
        f"- 输出视图：{view}",
        "",
        "## 快速判断",
        "",
    ]
    for item in takeaways:
        lines.append(f"- {item}")
    lines.append("")

    for section in SECTION_ORDER:
        hits = grouped_hits.get(section, [])
        if not hits:
            continue
        lines.append(f"## {SECTION_LABELS[section]}")
        lines.append("")
        for hit in hits:
            lines.append(f"- [{hit.title}]({hit.url})")
            if view in {"brief", "report"}:
                lines.append(f"  来源：`{hit.domain}`")
                if hit.content:
                    lines.append(f"  摘要：{hit.content}")
            if view == "report":
                lines.append(f"  检索词：`{hit.query}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def to_json_payload(
    topic: str,
    profile_name: str,
    grouped_hits: Dict[str, List[SearchHit]],
    takeaways: Sequence[str],
    search_runs: Sequence[dict],
) -> dict:
    return {
        "topic": topic,
        "profile": profile_name,
        "profile_summary": TOPIC_PROFILES[profile_name]["summary"],
        "takeaways": list(takeaways),
        "sections": {
            section: [
                {
                    "title": hit.title,
                    "url": hit.url,
                    "domain": hit.domain,
                    "summary": hit.content,
                    "query": hit.query,
                    "score": hit.score,
                }
                for hit in grouped_hits.get(section, [])
            ]
            for section in SECTION_ORDER
        },
        "search_runs": list(search_runs),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research an AI topic using Tavily-backed web search.")
    parser.add_argument("topic", help="Topic to research, e.g. MCP, RAG, AI Coding Agent")
    parser.add_argument("--view", choices=["quick", "brief", "report"], default="brief")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--max-per-section", type=int, default=DEFAULT_MAX_PER_SECTION)
    parser.add_argument("--queries-per-section", type=int, default=DEFAULT_QUERIES_PER_SECTION)
    parser.add_argument("--search-depth", choices=["basic", "advanced"], default=DEFAULT_SEARCH_DEPTH)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Days window for the latest/news section")
    parser.add_argument("--include-domains", default="", help="Extra domains to include, comma-separated")
    parser.add_argument("--exclude-domains", default="", help="Extra domains to exclude, comma-separated")
    parser.add_argument("--output", help="Optional file path to write the rendered result")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_local_env()

    include_domains = split_csv(args.include_domains)
    exclude_domains = DEFAULT_EXCLUDE_DOMAINS + split_csv(args.exclude_domains)
    profile_name = detect_profile(args.topic)
    search_topic, intent_terms = resolve_topic_alias(args.topic)
    queries_by_section = build_queries(search_topic, profile_name)

    hits, search_runs = collect_hits(
        search_topic=search_topic,
        queries_by_section=queries_by_section,
        search_depth=args.search_depth,
        days=args.days,
        queries_per_section=args.queries_per_section,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        intent_terms=intent_terms,
    )
    grouped_hits = dedupe_and_rank(hits, max_per_section=max(1, args.max_per_section))
    takeaways = build_takeaways(args.topic, profile_name, grouped_hits)

    if args.format == "json":
        rendered = json.dumps(
            to_json_payload(args.topic, profile_name, grouped_hits, takeaways, search_runs),
            ensure_ascii=False,
            indent=2,
        )
    else:
        rendered = render_markdown(args.topic, profile_name, grouped_hits, takeaways, args.view)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + ("" if rendered.endswith("\n") else "\n"), encoding="utf-8")
        print(str(out_path))
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
