---
name: ai-topic-research
description: 面向 AI 技术主题和技术社区热点的联网研究 skill。既能研究单个主题，如 MCP、A2A、RAG、AI Coding Agent、Responses API、LangGraph，也能先从技术社区发现最近比较热门的技术方向和观点，再整理成结构化摘要。
---

# AI Topic Research

这个 skill 有两种模式：

- `topic`：把一个简短的 AI 技术主题整理成研究摘要
- `discover`：先从技术社区里找最近大家在热议什么技术、什么观点，再输出候选方向

它依赖仓库里的 `tavily-search` skill：脚本会直接调用 `skills/tavily-search/scripts/tavily_search.py` 做联网搜索，再进行去重、打分、分组和渲染。

## 适用场景

- 用户只给一个 AI 技术词，希望快速了解全貌
- 用户还没确定具体主题，想先看技术社区最近在聊什么
- 需要先找官方资料，再补最新动态和实战案例
- 需要面向技术研究做“第一轮资料收集”
- 想把搜索结果整理成 Markdown 或 JSON 给后续 skill 继续处理

## 默认研究维度

### `discover` 模式

- 热门技术方向
- 热门观点 / 争议
- 值得继续追的关键词

### `topic` 模式

- 官方文档 / 官方博客
- 最新动态 / 新闻
- 教程 / 实战文章
- 开源项目 / GitHub
- 对比 / 差异化观点

## 环境变量

优先沿用 `tavily-search` 的配置：

- `TAVILY_API_KEYS`
- `TAVILY_API_KEY`
- `TAVILY_SEARCH_BASE_URL`

脚本也会尝试读取：

- 当前 skill 下的 `.env.local` / `.env`
- `skills/tavily-search/` 下的 `.env.local` / `.env`

## 使用方式

### 先发现社区热点

```bash
python3 scripts/ai_topic_research.py --mode discover
```

### 带一个种子方向去发现热点

```bash
python3 scripts/ai_topic_research.py "agent engineering" --mode discover
```

### 直接研究一个主题

```bash
python3 scripts/ai_topic_research.py "MCP"
```

### 输出更完整的主题报告

```bash
python3 scripts/ai_topic_research.py "AI Coding Agent" \
  --mode topic \
  --view report \
  --max-per-section 4
```

### 输出 JSON 给后续流程

```bash
python3 scripts/ai_topic_research.py "Responses API" \
  --format json \
  --output /tmp/responses-api-research.json
```

## 常用参数

- `topic`：主题词，例如 `MCP`、`A2A`、`RAG`；在 `discover` 模式下可选，表示种子方向
- `--mode`：`topic` 或 `discover`
- `--view`：`quick`、`brief`、`report`
- `--format`：`markdown` 或 `json`
- `--max-per-section`：每个研究维度最多保留多少条
- `--queries-per-section`：每个研究维度最多发起多少个搜索词，默认 2
- `--discover-queries`：`discover` 模式下最多发起多少个社区趋势查询
- `--search-depth`：`basic` 或 `advanced`
- `--days`：新闻维度最近多少天，默认 30
- `--include-domains`：额外限制域名，逗号分隔
- `--exclude-domains`：额外排除域名，逗号分隔
- `--output`：保存到文件

## 工作流程

### `discover` 模式

1. 用一组社区趋势查询词扫描技术社区来源
2. 聚类成若干热门技术方向
3. 额外提取更有热度的观点 / 争议
4. 输出热点、代表链接和后续值得继续追的关键词

### `topic` 模式

1. 判断主题更像协议、模型 / API、工程实践，还是开源框架
2. 按主题类型扩展搜索词
3. 分维度调用 `tavily-search`
4. 对结果做 URL 去重和相关性打分
5. 按“官方 / 最新 / 教程 / 开源 / 对比”分组输出

## 使用建议

- 如果你还没确定具体要研究什么，先跑 `--mode discover`
- 技术主题越短越好，通常 1 到 4 个词最准
- 如果你只关心官方资料，可以加 `--include-domains openai.com,platform.openai.com,github.com`
- 如果准备喂给写作类 skill，优先用 `--view report`
