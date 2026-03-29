---
name: tavily-search
description: 使用 Tavily Search API 做联网搜索。支持配置多个 API Keys，随机选 key 调用；若当前 key 失效或鉴权失败，会自动尝试下一个 key。适用于需要实时网页搜索、新闻检索、资料汇总、事实核查的场景。
---

# Tavily Search

这个 skill 通过本地脚本调用 Tavily Search API，支持多 Key 轮换和失败回退。

## 环境变量

至少配置以下其中一个：

- `TAVILY_API_KEYS` — 多个 key，推荐。支持逗号、换行、空格分隔
- `TAVILY_API_KEY` — 单个 key，兼容模式
- `TAVILY_SEARCH_BASE_URL` — 可选，默认 `https://api.tavily.com`

示例：

```bash
export TAVILY_API_KEYS="tvly-dev-aaa,tvly-dev-bbb,tvly-dev-ccc"
export TAVILY_SEARCH_BASE_URL="https://api.tavily.com"
```

## 能力

- 随机选择一个 key 开始请求
- 如果当前 key 鉴权失败、过期、额度异常或返回 401/403/429，会自动尝试其他 key
- 支持限制结果条数、主题、时间范围、是否抓取正文
- 支持指定包含/排除的搜索域名
- 输出结构化 JSON，方便后续 agent 二次处理

## 使用方法

### 直接搜索

```bash
python3 scripts/tavily_search.py "OpenClaw ACP runtime sessions" \
  --topic general \
  --max-results 5 \
  --output /tmp/tavily-results.json
```

### 常用参数

- `query`：搜索词
- `--topic`：`general` 或 `news`
- `--max-results`：返回结果数量，默认 5
- `--days`：仅新闻主题时可选，限制最近多少天
- `--include-answer`：让 Tavily 返回总结答案
- `--include-raw-content`：抓取原文正文
- `--include-domains`：只搜指定域名，逗号分隔
- `--exclude-domains`：排除指定域名，逗号分隔
- `--output`：保存 JSON 到文件

## 工作流程

1. 理解用户要搜什么
2. 组织好查询词
3. 调用脚本搜索
4. 如果某个 key 失败，自动切下一个
5. 整理结果返回给用户

## 失败回退策略

脚本会把可用 keys 打乱顺序，然后依次尝试：

- 当前 key 成功：立即返回
- 当前 key 鉴权/限流失败：继续试下一个
- 所有 key 都失败：返回完整错误摘要，便于排查

## 示例

```bash
python3 scripts/tavily_search.py "Tavily API pricing" --topic general --max-results 3
```

指定搜索站点：

```bash
python3 scripts/tavily_search.py "AI" --topic news --include-domains techcrunch.com,theverge.com --max-results 5
```
