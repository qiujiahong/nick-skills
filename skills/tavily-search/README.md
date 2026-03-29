# tavily-search

Tavily 搜索 skill。

特性：

- 支持 `TAVILY_API_KEYS` 多 key 注入
- 每次请求随机从某个 key 开始
- key 失效、401/403/429 时自动回退到其他 key
- 可选 general/news 主题
- 支持 include/exclude domains
- 输出结构化 JSON

## 环境变量

```bash
export TAVILY_API_KEYS="tvly-aaa,tvly-bbb,tvly-ccc"
# 或兼容单 key
export TAVILY_API_KEY="tvly-aaa"
export TAVILY_SEARCH_BASE_URL="https://api.tavily.com"
```

## 用法

```bash
python3 scripts/tavily_search.py "OpenClaw skills" --max-results 5
```

指定站点范围：

```bash
python3 scripts/tavily_search.py "AI" --topic news --include-domains techcrunch.com,theverge.com --max-results 5
```

保存到文件：

```bash
python3 scripts/tavily_search.py "OpenClaw skills" --max-results 5 --output /tmp/tavily.json
```
