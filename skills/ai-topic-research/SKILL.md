---
name: ai-topic-research
description: 面向 AI 技术主题的联网研究 skill。适合用户只给一个粗主题词，如 MCP、A2A、RAG、AI Coding Agent、Responses API、LangGraph，然后自动扩展查询词，调用 tavily-search 搜索官方文档、最新进展、实战教程、开源项目和对比观点，并整理成结构化摘要。
---

# AI Topic Research

这个 skill 用来把一个简短的 AI 技术主题，整理成一份可读的研究摘要，而不是只返回零散链接。

它依赖仓库里的 `tavily-search` skill：脚本会直接调用 `skills/tavily-search/scripts/tavily_search.py` 做联网搜索，再进行去重、打分、分组和渲染。

## 适用场景

- 用户只给一个 AI 技术词，希望快速了解全貌
- 需要先找官方资料，再补最新动态和实战案例
- 需要面向技术研究做“第一轮资料收集”
- 想把搜索结果整理成 Markdown 或 JSON 给后续 skill 继续处理

## 默认研究维度

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

### 直接研究一个主题

```bash
python3 scripts/ai_topic_research.py "MCP"
```

### 输出更完整的报告

```bash
python3 scripts/ai_topic_research.py "AI Coding Agent" \
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

- `topic`：主题词，例如 `MCP`、`A2A`、`RAG`
- `--view`：`quick`、`brief`、`report`
- `--format`：`markdown` 或 `json`
- `--max-per-section`：每个研究维度最多保留多少条
- `--queries-per-section`：每个研究维度最多发起多少个搜索词，默认 2
- `--search-depth`：`basic` 或 `advanced`
- `--days`：新闻维度最近多少天，默认 30
- `--include-domains`：额外限制域名，逗号分隔
- `--exclude-domains`：额外排除域名，逗号分隔
- `--output`：保存到文件

## 工作流程

1. 判断主题更像协议、模型 / API、工程实践，还是开源框架
2. 按主题类型扩展搜索词
3. 分维度调用 `tavily-search`
4. 对结果做 URL 去重和相关性打分
5. 按“官方 / 最新 / 教程 / 开源 / 对比”分组输出

## 使用建议

- 技术主题越短越好，通常 1 到 4 个词最准
- 如果你只关心官方资料，可以加 `--include-domains openai.com,platform.openai.com,github.com`
- 如果准备喂给写作类 skill，优先用 `--view report`
