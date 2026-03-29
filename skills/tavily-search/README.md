# tavily-search

一个给 OpenClaw / Agent Skills 用的 Tavily 搜索 skill，支持多 API Key 轮换、随机选 key、失效自动回退，以及按站点范围过滤搜索结果。

## 功能

- 支持 `TAVILY_API_KEYS` 注入多个 keys
- 每次请求随机打乱 key 顺序
- 当前 key 401 / 403 / 429 / 失效时自动尝试下一个
- 支持 `general` / `news` 两种搜索主题
- 支持限制结果数、搜索深度、近 N 天新闻
- 支持 `include_domains` / `exclude_domains`
- 输出结构化 JSON，适合 agent 二次处理

## 目录结构

```text
skills/tavily-search/
├── SKILL.md
├── README.md
├── .env.example
└── scripts/
    └── tavily_search.py
```

## 环境变量

至少配置以下其中一个：

### 推荐：多个 API Keys

```bash
export TAVILY_API_KEYS="tvly-key-1,tvly-key-2,tvly-key-3"
```

也支持换行分隔：

```bash
export TAVILY_API_KEYS=$'tvly-key-1\ntvly-key-2\ntvly-key-3'
```

### 兼容：单个 API Key

```bash
export TAVILY_API_KEY="tvly-key-1"
```

### 可选：自定义 API 地址

```bash
export TAVILY_SEARCH_BASE_URL="https://api.tavily.com"
```

## Key 选择与回退策略

脚本的行为是：

1. 从 `TAVILY_API_KEYS` / `TAVILY_API_KEY` 中收集所有可用 key
2. 自动去重
3. 每次请求前随机打乱顺序
4. 依次尝试 key
5. 如果某个 key 返回以下情况，会继续尝试下一个：
   - `401 Unauthorized`
   - `403 Forbidden`
   - `429 Too Many Requests`
   - 网络异常 / 请求异常
6. 任意一个 key 成功即返回结果
7. 如果全部失败，返回完整失败摘要

这意味着：
- 不会固定只吃同一把 key
- 单 key 挂掉不会导致整个 skill 直接失效
- 多个 agent 共用同一组 key 也更稳一点

## 脚本用法

### 基础搜索

```bash
python3 scripts/tavily_search.py "OpenClaw skills" --max-results 5
```

### 搜新闻

```bash
python3 scripts/tavily_search.py "AI" --topic news --days 7 --max-results 5
```

### 返回 Tavily answer

```bash
python3 scripts/tavily_search.py "OpenClaw ACP" --include-answer
```

### 包含原文正文

```bash
python3 scripts/tavily_search.py "OpenClaw skills" --include-raw-content
```

### 只搜指定站点

```bash
python3 scripts/tavily_search.py "AI" \
  --topic news \
  --include-domains techcrunch.com,theverge.com \
  --max-results 5
```

### 排除指定站点

```bash
python3 scripts/tavily_search.py "AI" \
  --exclude-domains pinterest.com,reddit.com \
  --max-results 5
```

### 保存结果到文件

```bash
python3 scripts/tavily_search.py "OpenClaw skills" \
  --max-results 5 \
  --output /tmp/tavily-results.json
```

## 参数说明

- `query`：搜索词
- `--topic`：`general` 或 `news`
- `--max-results`：返回结果数量，默认 `5`
- `--search-depth`：`basic` 或 `advanced`
- `--days`：仅新闻主题使用，限制最近多少天
- `--include-answer`：返回 Tavily 总结答案
- `--include-raw-content`：抓取原文正文
- `--include-images`：返回图片结果
- `--include-domains`：仅保留指定域名结果，逗号分隔
- `--exclude-domains`：排除指定域名结果，逗号分隔
- `--output`：把 JSON 保存到文件

## 输出格式

成功时大致返回：

```json
{
  "ok": true,
  "used_key": "tvly...abcd",
  "topic": "news",
  "query": "AI",
  "response": {
    "results": []
  }
}
```

失败时大致返回：

```json
{
  "ok": false,
  "query": "AI",
  "topic": "news",
  "failures": [
    {
      "key": "tvly...abcd",
      "status": 401,
      "error": {
        "detail": {
          "error": "Unauthorized: missing or invalid API key."
        }
      }
    }
  ]
}
```

## 适合的使用场景

- 让 agent 搜实时网页结果
- 让 agent 搜最近新闻
- 指定站点搜索，比如只搜某个博客、媒体、文档站
- 多 key 环境下尽量提高稳定性
- 需要结构化 JSON 给后续流程继续处理

## 注意事项

- Tavily 的实际返回质量会受 query 本身影响很大
- 如果站点名本身就含某个关键词，可能会出现“站内泛匹配”
- 域名过滤是结果范围控制，不等于站内精准全文搜索
- 多 key 只能降低单点故障，不能保证上游服务永远可用

## 示例：搜索掘金 AI Coding 站

```bash
python3 scripts/tavily_search.py "Cursor" \
  --include-domains aicoding.juejin.cn \
  --max-results 5
```

比起直接搜 `AI`，这种更具体的词通常更准。
