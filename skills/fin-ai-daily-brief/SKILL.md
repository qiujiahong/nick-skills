---
name: fin-ai-daily-brief
description: 基于 Google 搜索“金融 AI”，忽略赞助商结果与 AI 概览，提取前 15 条自然结果并筛选出对金融企业更有价值的 10 条，生成单页面 HTML 资讯简报并通过 SMTP 发送给订阅用户。
metadata:
  openclaw:
    os: [darwin, linux]
    requires:
      bins: [python3]
---

# Fin AI Daily Brief

这个 skill 用来产出一份面向金融企业的 AI 资讯日报，并发送给订阅邮箱。

## 严格工作流

1. 打开 `https://www.google.com/`
2. 搜索 `金融 AI`
3. 忽略 **赞助商搜索结果**
4. 忽略 **AI 概览**
5. 提取前 **15 条自然搜索结果**：
   - 标题
   - URL
   - 内容总结
6. 从这 15 条里筛选出 **10 条对金融企业更有价值** 的资讯
7. 生成单页面 HTML 前端
8. 通过 SMTP 发送给订阅邮箱

## 默认订阅用户

初始订阅用户：

```bash
FIN_AI_SUBSCRIBERS=qiujiahongde@163.com
```

未来新增订阅用户可通过以下两种方式：

- 继续扩展 `FIN_AI_SUBSCRIBERS`
- 使用 `FIN_AI_SUBSCRIBERS_FILE` / `--subscribers-file`

## 配置项

### SMTP

- `FIN_AI_SMTP_HOST`：SMTP 主机
- `FIN_AI_SMTP_PORT`：SMTP 端口，163 邮箱常用 `465`
- `FIN_AI_SMTP_USER`：SMTP 用户名 / 发件邮箱
- `FIN_AI_SMTP_PASS`：SMTP 授权码
- `FIN_AI_SMTP_FROM`：发件人地址，不填默认取 `FIN_AI_SMTP_USER`
- `FIN_AI_SMTP_USE_SSL`：是否使用 SSL，默认 `true`
- `FIN_AI_SUBSCRIBERS`：默认订阅邮箱列表
- `FIN_AI_SUBSCRIBERS_FILE`：可选，订阅用户文件

### 搜索输入

#### 推荐：Google 浏览器结果 JSON

推荐在 agent/browser 环境中先把 Google 前 15 条自然结果整理成 JSON，再喂给脚本：

```json
{
  "query": "金融 AI",
  "results": [
    {
      "title": "标题",
      "url": "https://example.com/article",
      "summary": "摘要",
      "source": "example.com"
    }
  ]
}
```

脚本会自动：

- 截断为前 15 条
- 忽略带 `is_sponsored=true` 的结果
- 忽略 `type=ai_overview / sponsored / ad` 的结果
- 过滤 Google 自己的跳转 / 广告链接

#### 回退：Tavily 搜索

如果暂时拿不到 Google JSON，也可用 Tavily 回退验证：

- `TAVILY_API_KEYS` 或 `TAVILY_API_KEY`
- `TAVILY_SEARCH_BASE_URL`

## 用法

### 方式 1：严格按 Google 工作流执行

```bash
python3 scripts/generate_fin_ai_brief.py \
  --query "金融 AI" \
  --input-results ./output/google-results.json \
  --output-dir ./output \
  --send-email
```

### 方式 2：指定订阅文件

```bash
python3 scripts/generate_fin_ai_brief.py \
  --query "金融 AI" \
  --input-results ./output/google-results.json \
  --subscribers-file ./subscribers.txt \
  --output-dir ./output \
  --send-email
```

### 方式 3：没有 Google JSON 时使用 Tavily 回退

```bash
python3 scripts/generate_fin_ai_brief.py \
  --query "金融 AI" \
  --output-dir ./output \
  --send-email
```

## 输出产物

- `search-result.json`
- `candidates.json`：前 15 条候选
- `selected.json`：精选 10 条
- `brief.html`：单页面前端
- `brief.txt`：纯文本版本

## 价值判断标准

精选时优先保留：

- 银行、券商、保险、资管、支付、风控、合规、投研相关
- 有明确业务落地、运营增效、监管或模型治理价值
- 对金融机构管理层、分析师、创新与数字化团队更有参考价值

优先忽略：

- 广告 / 赞助商结果
- AI 概览
- 软文、标题党、SEO 垃圾页
- 泛娱乐、泛消费类 AI 新闻
- 对金融企业实际价值弱的内容
