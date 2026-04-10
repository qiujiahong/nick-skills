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
DEFAULT_DISCOVER_QUERIES = 5
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
COMMUNITY_SOURCE_DOMAINS = [
    "news.ycombinator.com",
    "simonwillison.net",
    "latent.space",
    "infoq.com",
    "github.blog",
    "developers.googleblog.com",
    "martinfowler.com",
    "huggingface.co",
    "blog.langchain.dev",
    "every.to",
    "stratechery.com",
    "thenewstack.io",
    "zilliz.com",
    "adopt.ai",
]
DISCOVERY_QUERIES = [
    "AI engineering trends agents MCP A2A coding agents",
    "developer discussion MCP A2A agent protocol AI",
    "AI coding agents production lessons developers",
    "RAG long context agent memory evals developer discussion",
    "browser agents computer use developer discussion AI",
    "model routing small models cost latency developer discussion AI",
]
TREND_THEMES = {
    "agent_protocols": {
        "label": "Agent 协议与互操作",
        "keywords": ["mcp", "model context protocol", "a2a", "agent2agent", "protocol", "interop", "interoperability"],
        "tags": ["mcp", "a2a", "protocols"],
    },
    "coding_agents": {
        "label": "AI Coding Agents",
        "keywords": ["coding agent", "code agent", "claude code", "cursor", "openhands", "swe-agent", "repo agent"],
        "tags": ["coding-agents", "claude-code", "cursor"],
    },
    "browser_agents": {
        "label": "Browser / Computer Use Agents",
        "keywords": ["browser agent", "browser use", "computer use", "operator", "comet", "web agent"],
        "tags": ["browser-agents", "computer-use"],
    },
    "rag_memory": {
        "label": "RAG、长上下文与记忆",
        "keywords": ["rag", "retrieval", "long context", "memory", "knowledge base", "vector search"],
        "tags": ["rag", "memory", "long-context"],
    },
    "evals_observability": {
        "label": "Evals、Observability 与 Agent 可靠性",
        "keywords": ["eval", "evaluation", "observability", "trace", "benchmark", "reliability", "tool call"],
        "tags": ["evals", "observability", "reliability"],
    },
    "workflow_orchestration": {
        "label": "Workflow 编排与 Agent Framework",
        "keywords": ["langgraph", "workflow", "orchestration", "autogen", "crewai", "mastra", "graph"],
        "tags": ["workflow", "orchestration", "frameworks"],
    },
    "model_routing": {
        "label": "模型路由、小模型与成本优化",
        "keywords": ["model routing", "small model", "latency", "cost", "budget", "distillation", "reasoning model"],
        "tags": ["routing", "small-models", "latency"],
    },
}
VIEWPOINT_THEMES = {
    "workflows_vs_agents": {
        "label": "很多生产场景更像 workflow，不是越多 agent 越好",
        "keywords": ["workflows over agents", "workflow", "agents", "orchestration", "production"],
        "tags": ["workflow-vs-agents"],
    },
    "evals_over_vibes": {
        "label": "评测、harness 和工具调用成功率，比“模型主观感觉更强”更重要",
        "keywords": ["eval", "harness", "tool call", "structured output", "reliability", "benchmark"],
        "tags": ["evals", "tool-calling"],
    },
    "rag_vs_long_context": {
        "label": "RAG 不是被长上下文替代，而是在检索质量和成本上重新分工",
        "keywords": ["rag", "long context", "retrieval", "context window", "tradeoff"],
        "tags": ["rag-vs-long-context"],
    },
    "protocols_matter": {
        "label": "Agent 协议开始从概念讨论走向工程互操作",
        "keywords": ["mcp", "a2a", "protocol", "interop", "tool", "agent2agent"],
        "tags": ["mcp", "a2a", "interop"],
    },
    "small_models_win": {
        "label": "最佳模型不是单点最强，而是 workload × harness × budget 的组合",
        "keywords": ["small model", "latency", "budget", "routing", "cost", "best model"],
        "tags": ["routing", "small-models", "cost"],
    },
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


@dataclass
class ClusterSummary:
    slug: str
    label: str
    tags: List[str]
    score: int
    hits: List[SearchHit]


@dataclass
class BlogTopicRecommendation:
    topic: ClusterSummary
    angle: Optional[ClusterSummary]
    used_topics: List[str]
    fallback_used_topic: bool


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


def split_topic_list(value: str) -> List[str]:
    if not value:
        return []
    normalized = value.replace("\n", ",").replace(";", ",").replace("|", ",")
    return [part.strip() for part in normalized.split(",") if part.strip()]


def hostname_from_url(url: str) -> str:
    match = re.match(r"https?://([^/]+)", url or "")
    if not match:
        return ""
    return match.group(1).lower().removeprefix("www.")


def domain_matches(domain: str, patterns: Sequence[str]) -> bool:
    return any(domain == pattern or domain.endswith("." + pattern) for pattern in patterns)


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


def normalize_slug(value: str) -> str:
    lowered = normalize_text(value).lower()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", lowered)


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


def score_keyword_group(text: str, keywords: Sequence[str]) -> int:
    return sum(1 for keyword in keywords if keyword and keyword.lower() in text)


def build_queries(search_topic: str, profile_name: str) -> Dict[str, List[str]]:
    profile = TOPIC_PROFILES[profile_name]
    return {
        section: [template.format(topic=search_topic) for template in templates]
        for section, templates in profile["sections"].items()
    }


def build_discovery_queries(seed_topic: str = "") -> List[str]:
    queries = list(DISCOVERY_QUERIES)
    if seed_topic:
        queries.insert(0, f"{seed_topic} AI developer discussion trends")
        queries.insert(1, f"{seed_topic} agent engineering best practices discussion")
    return queries


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
                if include_domains and not domain_matches(domain, include_domains):
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


def collect_discovery_hits(
    seed_topic: str,
    search_depth: str,
    days: int,
    discover_queries: int,
    include_domains: Sequence[str],
    exclude_domains: Sequence[str],
) -> Tuple[List[SearchHit], List[dict]]:
    hits: List[SearchHit] = []
    search_runs: List[dict] = []
    queries = build_discovery_queries(seed_topic)[: max(1, discover_queries)]

    for query in queries:
        result = run_tavily_search(
            query=query,
            topic_kind="general",
            search_depth=search_depth,
            days=days,
            max_results=7,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
        search_runs.append({"query": query, "result": result})
        if not result.get("ok"):
            continue

        for item in result.get("response", {}).get("results", []):
            title = normalize_text(item.get("title") or "")
            url = normalize_text(item.get("url") or "")
            content = trim_text(item.get("content") or item.get("raw_content") or "")
            domain = hostname_from_url(url)
            if not title or not url:
                continue
            if include_domains and not domain_matches(domain, include_domains):
                continue
            base_score = source_bonus(domain) + keyword_score(query, query, title, content)
            hits.append(
                SearchHit(
                    section="community",
                    query=query,
                    title=title,
                    url=url,
                    content=content,
                    domain=domain,
                    score=base_score,
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


def dedupe_hits(hits: Sequence[SearchHit]) -> List[SearchHit]:
    deduped: List[SearchHit] = []
    seen_urls = set()
    for hit in sorted(hits, key=lambda item: (-item.score, item.domain, item.title)):
        canonical_url = canonicalize_url(hit.url)
        if canonical_url in seen_urls:
            continue
        deduped.append(hit)
        seen_urls.add(canonical_url)
    return deduped


def cluster_hits_by_taxonomy(
    hits: Sequence[SearchHit],
    taxonomy: Dict[str, dict],
    max_items: int,
) -> List[ClusterSummary]:
    buckets: Dict[str, List[SearchHit]] = {slug: [] for slug in taxonomy}

    for hit in dedupe_hits(hits):
        title_lower = hit.title.lower()
        content_lower = hit.content.lower()
        query_lower = hit.query.lower()
        best_slug = ""
        best_score = 0
        for slug, config in taxonomy.items():
            match_score = (
                score_keyword_group(title_lower, config["keywords"]) * 3
                + score_keyword_group(content_lower, config["keywords"])
                + score_keyword_group(query_lower, config["keywords"])
            )
            if match_score > best_score:
                best_slug = slug
                best_score = match_score
        if best_slug:
            boosted = SearchHit(
                section=hit.section,
                query=hit.query,
                title=hit.title,
                url=hit.url,
                content=hit.content,
                domain=hit.domain,
                score=hit.score + best_score * 8,
                raw=hit.raw,
            )
            buckets[best_slug].append(boosted)

    summaries: List[ClusterSummary] = []
    for slug, config in taxonomy.items():
        ranked_hits = sorted(buckets[slug], key=lambda item: (-item.score, item.domain, item.title))
        if not ranked_hits:
            continue
        chosen_hits: List[SearchHit] = []
        seen_domains = set()
        for hit in ranked_hits:
            if len(chosen_hits) >= max_items:
                break
            if hit.domain in seen_domains and len(ranked_hits) > max_items:
                continue
            chosen_hits.append(hit)
            seen_domains.add(hit.domain)
        total_score = sum(hit.score for hit in ranked_hits[: max_items + 2])
        summaries.append(
            ClusterSummary(
                slug=slug,
                label=config["label"],
                tags=list(config["tags"]),
                score=total_score,
                hits=chosen_hits,
            )
        )

    return sorted(summaries, key=lambda item: -item.score)


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


def build_discovery_takeaways(
    trend_summaries: Sequence[ClusterSummary],
    viewpoint_summaries: Sequence[ClusterSummary],
) -> List[str]:
    takeaways = []
    if trend_summaries:
        takeaways.append(f"社区讨论最密集的方向是“{trend_summaries[0].label}”。")
    if len(trend_summaries) > 1:
        takeaways.append(f"第二梯队热点是“{trend_summaries[1].label}”，说明它已经从概念走向落地讨论。")
    if viewpoint_summaries:
        takeaways.append(f"当前更有热度的观点不是单纯追新，而是“{viewpoint_summaries[0].label}”。")
    if not takeaways:
        takeaways.append("当前搜索结果里的社区热点不够集中，建议放宽时间窗口或补充中文社区源。")
    return takeaways[:4]


def summary_matches_used_topics(summary: ClusterSummary, used_topics: Sequence[str]) -> bool:
    if not used_topics:
        return False

    summary_forms = {
        normalize_slug(summary.slug),
        normalize_slug(summary.label),
    }
    for tag in summary.tags:
        summary_forms.add(normalize_slug(tag))

    for used in used_topics:
        used_form = normalize_slug(used)
        if not used_form:
            continue
        if used_form in summary_forms:
            return True
        if any(used_form in form or form in used_form for form in summary_forms if form):
            return True
    return False


def pick_blog_topic_recommendation(
    trend_summaries: Sequence[ClusterSummary],
    viewpoint_summaries: Sequence[ClusterSummary],
    used_topics: Sequence[str],
) -> Optional[BlogTopicRecommendation]:
    if not trend_summaries:
        return None

    chosen_topic = None
    fallback_used_topic = False
    for summary in trend_summaries:
        if summary_matches_used_topics(summary, used_topics):
            continue
        chosen_topic = summary
        break

    if chosen_topic is None:
        chosen_topic = trend_summaries[0]
        fallback_used_topic = True

    related_angle = None
    topic_tag_forms = {normalize_slug(tag) for tag in chosen_topic.tags}
    for summary in viewpoint_summaries:
        if summary_matches_used_topics(summary, used_topics):
            continue
        angle_tag_forms = {normalize_slug(tag) for tag in summary.tags}
        if topic_tag_forms & angle_tag_forms:
            related_angle = summary
            break

    return BlogTopicRecommendation(
        topic=chosen_topic,
        angle=related_angle,
        used_topics=list(used_topics),
        fallback_used_topic=fallback_used_topic,
    )


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


def render_discovery_markdown(
    seed_topic: str,
    days: int,
    recommendation: BlogTopicRecommendation,
) -> str:
    title = f"{seed_topic} 博客选题推荐" if seed_topic else "AI 博客选题推荐"
    topic = recommendation.topic
    angle = recommendation.angle
    lines = [
        f"# {title}",
        "",
        f"- 时间窗口：最近 {days} 天",
        f"- 推荐主题：{topic.label}",
        "",
        "## 选题",
        "",
    ]
    lines.append(f"- 主题：`{topic.label}`")
    lines.append(f"- 关键词：`{', '.join(topic.tags)}`")
    lines.append(f"- 热度信号：{topic.score}")
    if recommendation.used_topics:
        lines.append(f"- 已避开近 10 天主题：`{', '.join(recommendation.used_topics)}`")
    if recommendation.fallback_used_topic:
        lines.append("- 备注：候选都与已用主题重叠，这次退回到了热度最高的主题。")
    lines.append("")
    if angle:
        lines.append("## 推荐切口")
        lines.append("")
        lines.append(f"- {angle.label}")
        lines.append("")

    lines.append("## 支撑链接")
    lines.append("")
    for hit in topic.hits:
        lines.append(f"- [{hit.title}]({hit.url})")
        lines.append(f"  来源：`{hit.domain}`")
        if hit.content:
            lines.append(f"  摘要：{hit.content}")
    if angle:
        for hit in angle.hits[:1]:
            if all(hit.url != existing.url for existing in topic.hits):
                lines.append(f"- [{hit.title}]({hit.url})")
                lines.append(f"  来源：`{hit.domain}`")
                if hit.content:
                    lines.append(f"  摘要：{hit.content}")
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


def discovery_json_payload(
    seed_topic: str,
    days: int,
    recommendation: BlogTopicRecommendation,
    search_runs: Sequence[dict],
) -> dict:
    angle = recommendation.angle
    return {
        "mode": "discover",
        "seed_topic": seed_topic,
        "days": days,
        "community_sources": list(COMMUNITY_SOURCE_DOMAINS),
        "used_topics": recommendation.used_topics,
        "fallback_used_topic": recommendation.fallback_used_topic,
        "recommended_topic": {
            "slug": recommendation.topic.slug,
            "label": recommendation.topic.label,
            "tags": recommendation.topic.tags,
            "score": recommendation.topic.score,
            "hits": [
                {
                    "title": hit.title,
                    "url": hit.url,
                    "domain": hit.domain,
                    "summary": hit.content,
                    "query": hit.query,
                    "score": hit.score,
                }
                for hit in recommendation.topic.hits
            ],
        },
        "recommended_angle": None if angle is None else {
            "slug": angle.slug,
            "label": angle.label,
            "tags": angle.tags,
            "score": angle.score,
            "hits": [
                {
                    "title": hit.title,
                    "url": hit.url,
                    "domain": hit.domain,
                    "summary": hit.content,
                    "query": hit.query,
                    "score": hit.score,
                }
                for hit in angle.hits
            ],
        },
        "search_runs": list(search_runs),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research an AI topic using Tavily-backed web search.")
    parser.add_argument("topic", nargs="?", help="Topic to research, e.g. MCP, RAG, AI Coding Agent")
    parser.add_argument("--mode", choices=["topic", "discover"], help="topic=研究一个主题；discover=从社区里发现热点")
    parser.add_argument("--view", choices=["quick", "brief", "report"], default="brief")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--max-per-section", type=int, default=DEFAULT_MAX_PER_SECTION)
    parser.add_argument("--queries-per-section", type=int, default=DEFAULT_QUERIES_PER_SECTION)
    parser.add_argument("--discover-queries", type=int, default=DEFAULT_DISCOVER_QUERIES)
    parser.add_argument("--used-topics", default="", help="Recently used blog topics to avoid, separated by commas/newlines")
    parser.add_argument("--search-depth", choices=["basic", "advanced"], default=DEFAULT_SEARCH_DEPTH)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Days window for the latest/news section")
    parser.add_argument("--include-domains", default="", help="Extra domains to include, comma-separated")
    parser.add_argument("--exclude-domains", default="", help="Extra domains to exclude, comma-separated")
    parser.add_argument("--output", help="Optional file path to write the rendered result")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_local_env()

    mode = args.mode or ("discover" if not args.topic else "topic")
    include_domains = split_csv(args.include_domains)
    exclude_domains = DEFAULT_EXCLUDE_DOMAINS + split_csv(args.exclude_domains)
    used_topics = split_topic_list(args.used_topics)
    if mode == "discover":
        community_include_domains = include_domains or COMMUNITY_SOURCE_DOMAINS
        discovery_hits, search_runs = collect_discovery_hits(
            seed_topic=args.topic or "",
            search_depth=args.search_depth,
            days=args.days,
            discover_queries=args.discover_queries,
            include_domains=community_include_domains,
            exclude_domains=exclude_domains,
        )
        trend_summaries = cluster_hits_by_taxonomy(discovery_hits, TREND_THEMES, max_items=max(1, args.max_per_section))
        viewpoint_summaries = cluster_hits_by_taxonomy(discovery_hits, VIEWPOINT_THEMES, max_items=max(1, args.max_per_section))
        recommendation = pick_blog_topic_recommendation(trend_summaries, viewpoint_summaries, used_topics)
        if recommendation is None:
            raise SystemExit("discover mode did not find any candidate topics")

        if args.format == "json":
            rendered = json.dumps(
                discovery_json_payload(args.topic or "", args.days, recommendation, search_runs),
                ensure_ascii=False,
                indent=2,
            )
        else:
            rendered = render_discovery_markdown(args.topic or "", args.days, recommendation)
    else:
        if not args.topic:
            raise SystemExit("topic mode requires a topic")

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
