# 素材资料：OpenClaw 最流行的 5 个 skill 的使用方法

## 选择主题

OpenClaw 最流行的 5 个 skill 的使用方法

## 读者场景

- 刚开始用 OpenClaw 的用户
- 想给 OpenClaw 补第一批高频 skill 的用户
- 想知道哪些 skill 真正常用，而不是只看本地示例仓库的用户

## 排序依据

这篇文章里的“最流行”不是根据本地仓库里有哪些 skill 排出来的，而是按 2026-04-11 能查到的外部证据做交叉筛选：

1. ClawHub / OpenClaw Hub 可见的下载量和星标热度
2. 官方文档里常见的安装方式与 OpenClaw 技能生态说明
3. 社区文章里“优先安装”的重合项
4. 安全因素和通用性过滤

补充说明：

- `capability-evolver`、`wacli`、`byterover` 这类 skill 在某些榜单里下载量也很高，但社区安全讨论和通用性不如本次入选项稳定
- 本文优先选“新手装上之后马上能用、跨场景复用频率高”的 skill
- 因为 OpenClaw 生态里有同名或近似名称的 skill，正文安装步骤会优先建议先 `search` 再 `install`

## 入选的 5 个 skill

### 1. self-improving-agent

- 外部证据：
  - OpenClaw Hub 首页把它列进热门 skill，显示约 `15,962` 下载、`132` 星
  - 社区文章《35 OpenClaw Skills That Are Actually Worth Installing》把它列进“five to install first”
- 入选理由：
  - 高频、通用、差异化强
  - 和普通工具 skill 不同，它直接改变 OpenClaw 的长期工作方式
- 可写角度：
  - 它不是“再加一个工具”，而是给 OpenClaw 加一层长期记忆和纠错闭环
  - 越是重复性工作，收益越明显

### 2. Gog

- 外部证据：
  - OpenClaw Hub 首页热门 skill，显示约 `14,313` 下载、`48` 星
  - 社区文章把它列为第一批优先安装 skill，并强调 Gmail、Calendar、Drive、Docs、Sheets 的联动能力
- 入选理由：
  - 高度贴近日常办公
  - 一装就能覆盖邮件、日程、文档、表格多个高频场景
- 可写角度：
  - 它的价值不是单点查 Gmail，而是跨 Google Workspace 服务串动作

### 3. Summarize

- 外部证据：
  - OpenClaw Hub 首页热门 skill，显示约 `10,956` 下载、`28` 星
  - 社区文章给出的下载量约 `26.1K`，并把它列进“five to install first”
- 入选理由：
  - 上手门槛低，立刻能感受到效率提升
  - 几乎适用于文章、PDF、视频、长文档、会议记录等所有“先浓缩再处理”的场景
- 可写角度：
  - 它是最像“今天装上今天就能开始省时间”的 skill

### 4. Github

- 外部证据：
  - OpenClaw Hub 首页热门 skill，显示约 `10,611` 下载、`15` 星
  - 社区文章给出的下载量约 `24.8K`
  - 开发者文章里经常把 Github 列进第一批开发向 skill
- 入选理由：
  - 对开发者群体极其高频
  - 价值不在“连上 GitHub”，而在把 PR、Issue、CI 和日常问答接到 agent 工作流里
- 可写角度：
  - 从“看 GitHub”升级成“让 OpenClaw 帮你处理 GitHub”

### 5. Weather

- 外部证据：
  - 社区文章给出的下载量约 `21.1K`
  - 官方 popular 技能列表里长期能见到 Weather 类 skill
- 入选理由：
  - 功能简单，但组合价值高
  - 和日程、邮件、早报类工作流组合时非常顺手
- 可写角度：
  - 单独看很普通，放进 morning brief 流程里就变成高频基础能力

## 关键事实

- OpenClaw 官方文档说明可以通过 `openclaw skills search` 和 `openclaw skills install` 安装 ClawHub skill
- OpenClaw Hub 说明其数据来自 clawhub.ai API，可作为下载量与热度的辅助观测来源
- 社区“优先安装”类文章通常不会单纯按下载量排序，而会额外考虑安全性、稳定性和上手收益

## 关键观点

- “最流行”不等于“单纯下载最高”，更适合写成“最常被装到第一批工作流里的 5 个”
- 真正适合博客传播的切法不是逐条翻译 skill 描述，而是回答：
  - 为什么这 5 个最先被装
  - 它们分别解决什么日常动作
  - 新手应该先装哪一个
- 这篇文章需要明确提醒读者注意 ClawHub 生态的安全问题，建议安装前先搜索、核对作者和版本记录

## 可用案例

- self-improving-agent：
  - 重复写周报、日报、会议总结时，让 OpenClaw 记住你的格式偏好
- Gog：
  - “帮我看今天下午的会议，把相关邮件和 Drive 文档一起整理出来”
- Summarize：
  - “把这篇长文、这个 PDF、这个 YouTube 视频先压成 5 点摘要”
- Github：
  - “看一下昨晚失败的 CI，帮我归因成 3 类问题”
- Weather：
  - “给我一个早间简报：天气、日程、紧急邮件”

## 文章主线建议

文章不要写成“排行榜播报”，而是写成：

1. 先说明为什么要重新认真挑第一批 skill
2. 再交代这 5 个是怎么选出来的
3. 再逐个讲“它解决什么问题 + 最好怎么用”
4. 最后给出一条装机顺序建议

## 可用支撑链接

- 官方 CLI 安装说明：
  - https://docs.openclaw.ai/de/cli/index
- OpenClaw Hub 热门技能页：
  - https://openclaw-hub.org/
- 社区交叉筛选文章：
  - https://rentamac.io/best-openclaw-skills/
- 使用示例目录：
  - https://openclaw.army/
