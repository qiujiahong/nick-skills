---
name: fin-ai-daily-brief
description: 每日生成“金融 + AI”中文资讯简报：优先搜索中文内容，先搜索 20 条候选资讯，再筛选出对金融机构与分析师最有价值的 10 条，生成 HTML 前端页面，并通过 SMTP 发送给订阅邮箱。支持多个订阅人、可配置主题词、可本地落盘 HTML 与 JSON 结果。
metadata:
  openclaw:
    os: [darwin, linux]
    requires:
      bins: [python3]
---

# Fin AI Daily Brief

这个 skill 用来自动产出一份面向金融机构和分析师的“金融 + AI”中文资讯页，并通过 SMTP 发送邮件。

## 工作流程

1. 优先搜索中文来源的金融 + AI 相关资讯候选 20 条
2. 按“对金融机构与分析师的价值”进行排序与筛选，保留 10 条
3. 生成一个 HTML 前端资讯页面，内容包含：
   - 总览
   - 10 条资讯
   - 今日 AI 趣味知识分享（三句话）
4. 通过 SMTP 发送给订阅邮箱

## 适用场景

- 做金融行业 AI 中文资讯日报
- 给投研团队、分析师、创新部门、数字化团队推送外部信息
- 需要一个可直接投递的 HTML 邮件页面

## 搜索要求

- 默认优先搜索中文内容
- 查询词优先使用中文金融 AI 关键词扩展
- 筛选时优先保留中文标题、中文摘要、中文站点来源
- 对明显非中文、非金融、非 AI 相关内容进行过滤

## 环境变量

### 搜索

- `TAVILY_API_KEYS` 或 `TAVILY_API_KEY`：Tavily 搜索 API key
- `TAVILY_SEARCH_BASE_URL`：可选，默认 `https://api.tavily.com`

### SMTP

- `FIN_AI_SMTP_HOST`：SMTP 主机
- `FIN_AI_SMTP_PORT`：SMTP 端口，默认 `465`
- `FIN_AI_SMTP_USER`：SMTP 用户名
- `FIN_AI_SMTP_PASS`：SMTP 密码 / 授权码
- `FIN_AI_SMTP_FROM`：发件人地址；不填默认取 `FIN_AI_SMTP_USER`
- `FIN_AI_SMTP_USE_SSL`：是否使用 SSL，默认 `true`
- `FIN_AI_SUBSCRIBERS`：订阅邮箱列表，支持逗号 / 分号 / 换行分隔

默认建议把初始订阅邮箱放进去，例如：

```bash
export FIN_AI_SUBSCRIBERS="qiujiahongde@163.com"
```

## 使用方式

### 生成并发送日报

```bash
python3 scripts/generate_fin_ai_brief.py \
  --query "中文 金融 AI 应用 银行 券商 资管 保险 大模型 智能投研 风控 合规" \
  --date 2026-04-01 \
  --output-dir ./output \
  --send-email
```

### 只生成本地 HTML，不发邮件

```bash
python3 scripts/generate_fin_ai_brief.py --output-dir ./output
```

### 指定额外收件人

```bash
python3 scripts/generate_fin_ai_brief.py \
  --recipient analyst@example.com \
  --recipient strategy@example.com \
  --send-email
```

## 参数说明

- `--query`：搜索词；建议中文关键词
- `--date`：日报日期，默认当天
- `--top-k`：候选资讯数量，默认 20
- `--keep`：保留资讯数量，默认 10
- `--output-dir`：输出目录，默认 `./output`
- `--recipient`：额外收件人，可重复传入
- `--send-email`：生成后直接发邮件
- `--subject`：自定义邮件标题

## 输出产物

脚本会输出：

- `candidates.json`：20 条候选资讯
- `selected.json`：筛选后的 10 条资讯
- `brief.html`：HTML 页面
- `brief.txt`：纯文本摘要

## 价值判断标准

筛选时优先保留：

- 中文来源、中文标题、中文摘要
- 与银行、券商、保险、资管、支付、风控、合规、投研、客服、运营直接相关
- 有明确业务落地、监管影响、生产效率影响、模型能力升级、数据基础设施变化
- 信息源相对可信，内容新，且不只是泛泛而谈

相对降权：

- 纯营销软文
- 过于泛化的 AI 科普
- 对金融业务没有实际映射的资讯
- 重复、低质量或标题党内容
- 非中文内容
