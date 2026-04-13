---
name: fin-ai-daily-brief
description: 基于仓库内 tavily-search skill 搜索“金融 AI”，返回前 15 条结果（标题、URL、内容总结），筛选出对金融企业更有价值的 10 条，生成单页面 HTML 资讯简报并通过 SMTP 发送给订阅用户。
metadata:
  openclaw:
    os: [darwin, linux]
    requires:
      bins: [python3]
---

# Fin AI Daily Brief

这个 skill 用来产出一份面向金融企业的 AI 资讯日报，并发送给订阅邮箱。

## 严格工作流

1. 使用仓库内 `skills/tavily-search/` skill 进行联网搜索
2. 搜索 `金融 AI`
3. 取前 **15 条结果**，保留：
   - 标题
   - URL
   - 内容总结
4. 忽略广告、赞助、低价值 SEO 页面
5. 从这 15 条里筛选出 **10 条对金融企业更有价值** 的资讯
6. 生成单页面 HTML 前端
7. 通过 SMTP 发送给订阅邮箱

## 默认订阅用户

初始订阅用户：

```bash
FIN_AI_SUBSCRIBERS=qiujiahongde@163.com
```

未来新增订阅用户可通过以下两种方式：

- 继续扩展 `FIN_AI_SUBSCRIBERS`
- 使用 `FIN_AI_SUBSCRIBERS_FILE` / `--subscribers-file`

## 配置项

### Tavily 搜索

- `TAVILY_API_KEYS`：多个 Tavily API keys，支持逗号分隔
- `TAVILY_SEARCH_BASE_URL`：默认 `https://api.tavily.com`
- 调用脚本：`skills/tavily-search/scripts/tavily_search.py`

### SMTP

- `FIN_AI_SMTP_HOST`：SMTP 主机
- `FIN_AI_SMTP_PORT`：SMTP 端口，163 邮箱常用 `465`
- `FIN_AI_SMTP_USER`：SMTP 用户名 / 发件邮箱
- `FIN_AI_SMTP_PASS`：SMTP 授权码
- `FIN_AI_SMTP_FROM`：发件人地址，不填默认取 `FIN_AI_SMTP_USER`
- `FIN_AI_SMTP_USE_SSL`：是否使用 SSL，默认 `true`
- `FIN_AI_SUBSCRIBERS`：默认订阅邮箱列表
- `FIN_AI_SUBSCRIBERS_FILE`：可选，订阅用户文件

## 用法

### 方式 1：直接通过 Tavily 搜索并发邮件

```bash
python3 scripts/generate_fin_ai_brief.py   --query "金融 AI"   --topic news   --output-dir ./output   --send-email
```

### 方式 2：指定订阅文件

```bash
python3 scripts/generate_fin_ai_brief.py   --query "金融 AI"   --topic news   --subscribers-file ./subscribers.txt   --output-dir ./output   --send-email
```

### 方式 3：使用已有结果 JSON

```bash
python3 scripts/generate_fin_ai_brief.py   --query "金融 AI"   --input-results ./output/tavily-results.json   --output-dir ./output   --send-email
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

- 广告 / 赞助内容
- 软文、标题党、SEO 垃圾页
- 泛娱乐、泛消费类 AI 新闻
- 对金融企业实际价值弱的内容
