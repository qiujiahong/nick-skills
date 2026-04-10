# 素材资料：OpenClaw 最流行的 5 个 skill 的使用方法

## 选择主题

OpenClaw 最流行的 5 个 skill 的使用方法

## 排序依据

这篇文章里的“最流行”不按本地仓库内容排序，而按 2026-04-11 可查到的外部资料交叉判断：

1. ClawHub / OpenClaw Hub 的下载量、星标和热门列表
2. 社区文章对“第一批值得安装”的推荐重合度
3. OpenClaw 官方文档里的技能安装路径
4. 安全性与通用性过滤

本次最终选择：

1. Gog
2. self-improving-agent
3. Summarize
4. Github
5. Weather

## 外部证据

OpenClaw Hub 首页展示了热门 skill 和下载/星标数据，并说明数据来自 clawhub.ai API。其热门列表中可见 `self-improving-agent`、`Gog`、`Summarize`、`Github` 等高频项。

Rentamac 在 2026-02-24 发布的社区筛选文章把 `Gog`、`self-improving-agent`、`Summarize`、`Github`、`Weather` 列为 “The five to install first”，并给出下载量、使用理由和安全提醒。

OpenClaw 官方 CLI 文档说明可以通过 `openclaw skills search`、`openclaw skills install` 和 `openclaw skills update` 安装/管理技能。

## 安全提醒

ClawHub 生态曾经出现过恶意 skill 事件，所以文章里必须提醒读者不要只按名字盲装。推荐使用顺序是：

先 search，核对名称、作者、版本和说明，再 install。对不熟悉的 skill，先在隔离环境或临时机器上测试。

## 每个 skill 的写作重点

### Gog

适合写成“办公动作联动器”。它的亮点不是读 Gmail，而是把 Gmail、Calendar、Drive、Docs、Sheets、Contacts 放进同一条任务链里。

可用例子：让 OpenClaw 查今天会议，找相关邮件，定位 Drive 文件，并生成跟进摘要。

### self-improving-agent

适合写成“让 OpenClaw 记住你的工作习惯”。它的亮点是把用户反复纠正过的偏好沉淀成长期工作流。

可用例子：周报格式、会议纪要字段、博客写作口吻、代码 review 关注点。

### Summarize

适合写成“输入压缩层”。它最容易让新用户感受到收益，因为文章、PDF、视频、会议内容都可以先浓缩再处理。

可用例子：把一篇技术长文压成 5 条结论，并标出值得继续深挖的部分。

### Github

适合写成“开发工作台”。它让 OpenClaw 不只是能看 GitHub，而是可以整理 PR、Issue、CI 和 review 反馈。

可用例子：早上让 OpenClaw 汇总昨晚失败的 CI，并按原因归类。

### Weather

适合写成“组合工作流的环境信息”。单独看普通，但和日程、邮件、早报组合后会变成高频入口。

可用例子：早间简报里合并天气、日程和紧急邮件。

## 文章结构建议

开头先回答“为什么不该乱装 skill”。中段交代排序依据，再逐个讲 5 个 skill 的使用方法。结尾给出安装顺序和安全建议。

文章不要在中间直接大段引用外部文章，而是把外部资料转成自己的判断。外部链接放在文末延伸阅读。

## 支撑链接

- OpenClaw Hub 热门技能数据：https://openclaw-hub.org/
- 社区筛选文章：https://rentamac.io/best-openclaw-skills/
- OpenClaw CLI 文档：https://docs.openclaw.ai/de/cli/index
