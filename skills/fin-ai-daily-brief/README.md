# fin-ai-daily-brief

面向金融机构与分析师的 AI 资讯日报 skill。

它会自动完成：

1. 搜索 20 条“金融 + AI”相关资讯
2. 筛选出最值得关注的 10 条
3. 生成 HTML 页面
4. 通过 SMTP 发给订阅邮箱

## 目录结构

```text
skills/fin-ai-daily-brief/
├── SKILL.md
├── README.md
├── .env.example
└── scripts/
    └── generate_fin_ai_brief.py
```

## 环境变量

```bash
# Tavily 搜索
TAVILY_API_KEYS=tvly-key-1,tvly-key-2
TAVILY_SEARCH_BASE_URL=https://api.tavily.com

# SMTP
FIN_AI_SMTP_HOST=smtp.163.com
FIN_AI_SMTP_PORT=465
FIN_AI_SMTP_USER=your_mail@163.com
FIN_AI_SMTP_PASS=your_smtp_auth_code
FIN_AI_SMTP_FROM=your_mail@163.com
FIN_AI_SMTP_USE_SSL=true

# 默认订阅邮箱
FIN_AI_SUBSCRIBERS=qiujiahaongde@163.com
```

## 快速开始

只生成本地文件：

```bash
python3 scripts/generate_fin_ai_brief.py --output-dir ./output
```

生成并发邮件：

```bash
python3 scripts/generate_fin_ai_brief.py --output-dir ./output --send-email
```

## 邮件效果

邮件正文为 HTML 页面，包含：

- 今日总览
- 10 条高价值资讯卡片
- 今日 AI 趣味知识三句话

同时也会附带一个纯文本版本，方便邮件客户端回退显示。

## 默认搜索方向

默认 query 偏向这些方向：

- 金融 AI
- 银行大模型
- 券商 AI
- 智能投研
- 风控
- 合规
- 保险科技
- 资管科技
- 金融监管科技

## 筛选逻辑

不是简单按热度取前 10，而是按“对金融机构与分析师是否有实际价值”排序，优先保留：

- 可落地业务应用
- 监管 / 合规相关变化
- 投研 / 交易 / 客服 / 风控 / 运营效率提升
- 金融机构真实案例
- 基础设施和模型能力升级

## 说明

当前实现优先使用 Tavily 搜索结果与本地规则打分，不依赖额外 LLM API，因此更容易部署。

如果后续你要升级成：

- 自动定时发送
- 带后台管理订阅邮箱
- 多模板主题样式
- 接入数据库存历史简报
- 输出到网页站点

可以继续在这个 skill 上扩展。
