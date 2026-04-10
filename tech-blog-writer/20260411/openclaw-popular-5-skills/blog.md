# OpenClaw 最流行的 5 个 skill，应该怎么用？

很多人第一次配置 OpenClaw，都会犯同一个错误：看到 ClawHub 上有很多 skill，就想先装一堆。

但 OpenClaw 的体验不是靠数量堆出来的。真正影响效率的，往往是第一批 skill 有没有选对。第一批 skill 应该像“基础动作层”，帮你接住每天都在重复发生的任务，而不是变成一个很长但很少触发的插件清单。

所以这篇文章重新筛了一版更适合先装的 5 个 skill：`Gog`、`self-improving-agent`、`Summarize`、`Github` 和 `Weather`。

这里的“最流行”不是按本地仓库里有哪些 skill 来排，而是综合了 2026 年 4 月 11 日能查到的 ClawHub / OpenClaw Hub 热门数据、社区装机推荐、官方安装方式和安全因素。它们不一定是所有统计口径里的绝对前五，但很适合作为新手的第一批真实工作流。

[配图1](./assets/配图1-20260411-070144.png)

## 先说判断：不要先追求装得多

OpenClaw 的 skill 更像“给 agent 接上手和脚”，不是普通软件里的装饰性插件。

如果一个 skill 只能偶尔演示一次，它就不适合作为第一批安装项。第一批更应该覆盖几个高频动作：办公协作、长期偏好、内容压缩、开发流程和日常上下文。

这也是为什么我更推荐先装这 5 个。`Gog` 负责办公动作联动，`self-improving-agent` 负责沉淀你的工作习惯，`Summarize` 负责压缩长内容，`Github` 负责接入开发流程，`Weather` 则适合放进早报、日程和出行提醒这类组合工作流里。

## 1. Gog：把 Google Workspace 变成一条工作流

`Gog` 经常被推荐，是因为它不是单点工具。它把 Gmail、Calendar、Drive、Docs、Sheets、Contacts 这些能力放到 OpenClaw 可以调用的同一条链路里。

你可以把它理解成一个办公动作联动器。

最实用的用法不是“查一下 Gmail”，而是给 OpenClaw 一个跨服务任务。比如：

```text
看一下今天下午的客户会议，找出最近两封相关邮件，再把会议资料所在的 Drive 文件夹列出来，最后帮我写一段会前摘要。
```

安装前建议先搜：

```bash
openclaw skills search "gog"
openclaw skills install gog
```

如果你每天都在邮件、日程、文档和表格之间来回切，`Gog` 很可能是体感最强的第一个 skill。

[配图2](./assets/配图2-20260411-070144.png)

## 2. self-improving-agent：让 OpenClaw 记住你的工作习惯

`self-improving-agent` 的价值，不是多提供一个外部工具，而是让 OpenClaw 更像一个会积累经验的助手。

它适合处理那些你反复纠正 agent 的地方。比如周报要先写结论再写风险，会议纪要要保留 owner 和 deadline，博客草稿要少写定义、多写判断，代码 review 要优先看边界条件和失败路径。

更好的用法是主动给它明确反馈：

```text
以后写技术博客时，请先讲读者为什么要关心，再讲技术细节；结尾要给出适合谁现在跟进、谁可以观望。
```

安装方式同样建议先搜后装：

```bash
openclaw skills search "self-improving-agent"
openclaw skills install self-improving-agent
```

这个 skill 的收益不会像总结工具一样立刻爆发，但它会随着你使用次数增加而越来越明显。越是长期、重复、格式稳定的工作流，越适合让它参与。

## 3. Summarize：先压缩输入，再决定要不要深读

`Summarize` 是最容易今天装上、今天就感受到收益的 skill。

它解决的是一个很现实的问题：现在不是信息太少，而是信息太多。技术文章、PDF、会议记录、视频教程、长邮件，每一类都可能把你的注意力吃掉。

我的建议是，不要只对它说“总结一下”。更好的 prompt 是带上目标：

```text
把这篇文章总结成 5 条结论，面向技术负责人；另外标出 3 个值得继续读原文的段落。
```

安装：

```bash
openclaw skills search "summarize"
openclaw skills install summarize
```

一旦你开始把 `Summarize` 当成输入层，它就不只是一个摘要工具，而是你所有研究、阅读和判断之前的第一道过滤器。

[配图3](./assets/配图3-20260411-070144.png)

## 4. Github：把 PR、Issue 和 CI 变成 agent 工作台

如果你是开发者，`Github` 基本应该进入第一批安装。

它的价值不是“能访问 GitHub”，而是让 OpenClaw 帮你整理 GitHub 上发生的事情。你可以让它看 PR、Issue、CI、review 反馈，再把这些信息组织成可以行动的待办。

一个很实用的早晨任务是：

```text
看一下昨晚失败的 CI，把失败原因分成依赖问题、测试不稳定、真实代码回归三类，并给我一个优先处理顺序。
```

安装：

```bash
openclaw skills search "github"
openclaw skills install github
```

如果再配合 `self-improving-agent`，它还能逐渐记住你更关心哪类 CI 失败、喜欢怎样的 PR 摘要、以及 review 待办应该按什么格式输出。

## 5. Weather：看起来简单，但适合放进组合工作流

`Weather` 单独看并不酷。它不像 `Gog` 那样能串多个办公服务，也不像 `Github` 那样直接进入开发流程。

但它的优点正是简单、稳定、低门槛。真正的用法不是单独问天气，而是把它塞进早间简报或出门提醒。

比如：

```text
给我一个上班前简报：今天的天气、上午日程、需要提前处理的邮件，以及是否需要带伞。
```

安装：

```bash
openclaw skills search "weather"
openclaw skills install weather
```

这类 skill 的价值往往不是单点能力，而是让一个工作流更贴近日常生活。它很适合和 `Gog`、日程、邮件、提醒类 skill 一起用。

[配图4](./assets/配图4-20260411-070144.png)

## 我建议的安装顺序

如果你是新手，我建议先装 `Summarize`，因为它最容易立刻省时间。第二个装 `Gog`，把邮件、日程、文档和表格串起来。第三个装 `Github`，让开发工作流进入 OpenClaw。第四个装 `Weather`，补齐早报和日程上下文。最后装 `self-improving-agent`，开始沉淀长期偏好。

如果你是重度开发者，可以把 `Github` 提到第二个。如果你每天主要处理会议、邮件和文档，`Gog` 可以直接排第一。

真正重要的不是记住这 5 个名字，而是记住这 5 类能力：办公联动、长期习惯、输入压缩、开发流程和日常上下文。只要这 5 类能力先跑顺，后面再加更多细分 skill，才不会变成“装了很多，但没有形成工作流”。

最后提醒一句：ClawHub 生态很活跃，但也出现过恶意 skill 风险。安装前先 search，核对名称、作者、版本和说明；不熟悉的 skill 不要直接丢到主力环境里跑。

## 延伸阅读

OpenClaw Hub 热门技能数据：<https://openclaw-hub.org/>

社区装机筛选文章：<https://rentamac.io/best-openclaw-skills/>

OpenClaw CLI 文档：<https://docs.openclaw.ai/de/cli/index>
