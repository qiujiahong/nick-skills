# fin-ai-daily-brief

面向金融企业的 AI 资讯日报 skill。

这个版本按你的要求调整为 **Google 搜索优先且必须使用 Google 结果输入** 的工作流：

1. 打开 `https://www.google.com/`
2. 搜索 `金融 AI`
3. **忽略赞助商搜索结果**
4. **忽略 AI 概览**
5. 取前 15 条自然结果，保留每条的：标题、URL、内容总结
6. 对前 15 条再筛选出对金融企业更有价值的 10 条
7. 生成单页面 HTML 前端
8. 通过 SMTP 发送给订阅用户

## 目录结构

```text
skills/fin-ai-daily-brief/
├── SKILL.md
├── README.md
├── .env.example
├── .env.local.example
├── .gitignore
├── scripts/
│   └── generate_fin_ai_brief.py
└── output/
```

## 配置

### SMTP

本地 `.env.local` 示例：

```bash
FIN_AI_SMTP_HOST=smtp.163.com
FIN_AI_SMTP_PORT=465
FIN_AI_SMTP_USER=qiujiahongde@163.com
FIN_AI_SMTP_PASS=你的163邮箱SMTP授权码
FIN_AI_SMTP_FROM=qiujiahongde@163.com
FIN_AI_SMTP_USE_SSL=true
FIN_AI_SUBSCRIBERS=qiujiahongde@163.com
```

### 可扩展订阅用户

除 `FIN_AI_SUBSCRIBERS` 外，也支持单独的订阅文件：

```bash
python3 scripts/generate_fin_ai_brief.py \
  --input-results ./output/google-results.json \
  --subscribers-file ./subscribers.txt \
  --send-email
```

`subscribers.txt` 支持一行一个邮箱，也支持逗号 / 分号分隔。

## 推荐执行方式

### A. 按你的要求，使用 Google 浏览器结果作为输入

先把 Google 前 15 条自然结果整理成 JSON：

```json
{
  "query": "金融 AI",
  "results": [
    {
      "title": "原始标题",
      "zh_title": "中文标题",
      "url": "https://example.com/article",
      "summary": "原始摘要",
      "zh_summary": "中文摘要",
      "source": "example.com"
    }
  ]
}
```

然后生成页面并发邮件：

```bash
python3 scripts/generate_fin_ai_brief.py \
  --query "金融 AI" \
  --input-results ./output/google-results.json \
  --output-dir ./output \
  --send-email
```

### B. 必须提供 Google 结果 JSON

```bash
python3 scripts/generate_fin_ai_brief.py \
  --query "金融 AI" \
  --input-results ./output/google-results.json \
  --output-dir ./output \
  --send-email
```

> 当前版本不再走 Tavily / 通用回退搜索；必须由浏览器先拿到 Google 前 15 条自然结果，再交给脚本生成简报。

## 输出产物

脚本会输出：

- `search-result.json`：本次输入来源信息
- `candidates.json`：Google 前 15 条候选结果
- `selected.json`：精选后的 10 条高价值资讯
- `brief.html`：单页面前端 HTML
- `brief.txt`：纯文本邮件回退版本

## 页面结构

HTML 单页包含：

- 顶部总览 Hero
- Google 前 15 条结果
- 精选 10 条高价值资讯
- 今日 AI 趣味知识

## 筛选原则

精选 10 条时优先保留：

- 银行、券商、保险、资管、支付、风控、合规、投研相关
- 有明确业务落地价值
- 有监管、治理、模型风险、运营效率意义
- 对金融企业决策者、分析师、数字化团队更有参考价值

降权或忽略：

- 广告、软文、SEO 垃圾页
- 泛娱乐 / 泛消费 AI
- 与金融业务弱相关内容
- 与金融企业应用场景无映射的资讯
