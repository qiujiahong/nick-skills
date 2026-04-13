# fin-ai-daily-brief

面向金融企业的 AI 资讯日报 skill。

这个版本按你的要求调整为 **使用仓库内 `tavily-search` skill 搜索** 的工作流：

1. 复用 `skills/tavily-search` 的 Tavily 搜索能力；
2. 搜索 `金融 AI`；
3. 输出前 15 条候选结果，并为每条保留：标题、URL、内容总结；
4. 过滤广告、低价值页面、泛娱乐/泛消费类 AI 内容；
5. 从 15 条里保留 10 条对金融企业更有价值的资讯；
6. 生成单页面 HTML 前端；
7. 通过 SMTP 发送给订阅用户；
8. 默认订阅用户为 `qiujiahongde@163.com`，未来可继续追加。

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

### Tavily 搜索

本 skill 通过 `generate_fin_ai_brief.py` 调用：

- `skills/tavily-search/scripts/tavily_search.py`
- `TAVILY_API_KEYS`
- `TAVILY_SEARCH_BASE_URL=https://api.tavily.com`

本地 `.env.local` 可直接放在 `skills/fin-ai-daily-brief/`：

```bash
TAVILY_API_KEYS=tvly-xxx,tvly-yyy,tvly-zzz
TAVILY_SEARCH_BASE_URL=https://api.tavily.com
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
python3 scripts/generate_fin_ai_brief.py   --subscribers-file ./subscribers.txt   --send-email
```

`subscribers.txt` 支持一行一个邮箱，也支持逗号 / 分号分隔。

## 推荐执行方式

### A. 直接走 Tavily 搜索

```bash
python3 scripts/generate_fin_ai_brief.py   --query "金融 AI"   --topic news   --output-dir ./output   --send-email
```

### B. 使用预先收集的结果 JSON

如果你已在别处准备好结果，也可以传入：

```bash
python3 scripts/generate_fin_ai_brief.py   --query "金融 AI"   --input-results ./output/tavily-results.json   --output-dir ./output   --send-email
```

## 输出产物

脚本会输出：

- `search-result.json`：本次 Tavily 搜索与执行信息
- `candidates.json`：前 15 条候选结果
- `selected.json`：精选后的 10 条高价值资讯
- `brief.html`：单页面前端 HTML
- `brief.txt`：纯文本邮件回退版本

## 页面结构

HTML 单页包含：

- 顶部总览 Hero
- Tavily 搜索前 15 条结果
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
