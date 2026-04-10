# OpenClaw 最流行的 5 个 skill，应该怎么用？

如果你刚开始用 OpenClaw，最容易踩的一个坑不是模型没选对，而是 skill 装太杂。

OpenClaw 的生态已经很大了，ClawHub 上的 skill 数量也在持续增长。问题是，skill 变多以后，安装选择反而更难了。你当然可以一路往下翻排行榜，但真正决定体验的，通常不是“你装了多少”，而是“第一批装上的那几个，是不是足够高频、足够稳定、足够能立刻改变工作流”。

所以这篇文章不准备把本地仓库里现成的 skill 列一遍，而是按 2026 年 4 月 11 日能查到的外部热度、官方技能安装方式、以及社区装机优先级，重新筛一遍最值得先上手的 5 个 skill。

这 5 个 skill 分别是：

- `self-improving-agent`
- `Gog`
- `Summarize`
- `Github`
- `Weather`

它们不一定是所有榜单里“绝对下载最高”的前五，但它们是更接近“第一批最常被装进真实工作流里”的五个。判断标准很简单：热度足够高、社区反复推荐、功能足够通用、而且装上之后很快就能产生真实收益。

[配图1](./assets/配图1-20260411-062518.png)

## 先说结论：第一批 skill 不该追求多，而该追求能立刻接管动作

很多人刚接触 OpenClaw 时，会把 skill 理解成浏览器扩展，觉得多装几个总归没坏处。可真实情况恰恰相反。

当一个 skill 只是“可以装”，但你一个星期都不会主动调用它，它就不是第一批该装的 skill。第一批 skill 更像 OpenClaw 的基础动作层，应该直接接管你每天都在重复做的那类任务：

- 处理邮件和日程
- 读取长内容并压缩
- 跟进 GitHub 工作流
- 记住你反复纠正过的偏好
- 组合成一个早间或工作前简报

按这个标准看，`self-improving-agent`、`Gog`、`Summarize`、`Github` 和 `Weather` 非常像一个完整的起步组合。它们分别覆盖“会记住”“能串服务”“能压缩信息”“能接开发流程”“能补环境信息”这五种高频能力。

## 1. self-improving-agent：让 OpenClaw 真的开始越用越顺手

如果只选一个最能体现 OpenClaw 差异化的 skill，我会先选 `self-improving-agent`。

它最有价值的地方，不是帮你多做一件事，而是帮 OpenClaw 把你已经纠正过的事情记下来。你可以把它理解成一层面向工作流的长期偏好沉淀。

它最适合的场景包括：

- 你总是用固定结构写周报、日报、复盘
- 你总会要求 agent 按某种格式整理会议纪要
- 你反复要求它在输出里保留某些字段或删掉某些废话

更直接地说，普通 agent 的问题是每次都像重新认识你一次，而 `self-improving-agent` 的价值是把“你每次都会说的那句纠正”沉淀掉。

一个稳妥的安装方式是：

```bash
openclaw skills search "self-improving-agent"
openclaw skills install self-improving-agent
```

装好之后，不要急着把它当成“自动学习一切”的黑盒。更好的用法是主动给它重复反馈。比如你连续几次要求：

- 周报要先写结论，再写风险
- 会议纪要保留 action items 和 owner
- 博客草稿少一点定义，多一点判断

这类明确、可重复的纠偏最容易积累成长期收益。

## 2. Gog：为什么它经常被视为第一批必装 skill

`Gog` 的强，不在于“它能读 Gmail”这种单点能力，而在于它把 Gmail、Calendar、Drive、Docs、Sheets、Contacts 这些 Google Workspace 能力拉到了同一个动作面上。

这意味着很多你以前需要切多个标签页完成的动作，现在可以变成一句话。

最典型的用法是这些：

- 看完今天的会议后，把相关邮件和 Drive 文档一起捞出来
- 给某个联系人发一封跟进邮件，同时创建一个下周提醒
- 根据表格内容，生成一段对外更新摘要

安装时可以先搜再装：

```bash
openclaw skills search "gog"
openclaw skills install gog
```

它最适合的不是“偶尔查一个 Gmail”，而是下面这种跨服务动作：

“看一下今天下午 3 点的客户会议，找出最近两封相关邮件，再把会议资料所在的 Drive 文件夹列出来。”

一旦你开始这么用，就会明白为什么 `Gog` 经常被认为是 OpenClaw 生态里最像“生产力放大器”的 skill。

[配图2](./assets/配图2-20260411-062518.png)

## 3. Summarize：最容易今天装上、今天就省时间的 skill

如果你的日常里有大量长内容，`Summarize` 几乎是不会出错的一装就有感的 skill。

它的价值不复杂，但特别稳定：先压缩，再决定要不要深挖。

适合它的典型输入包括：

- 一篇太长的技术文章
- 一个 PDF 规格文档
- 一段会议录音或视频内容
- 一个你不想完整看完的教程

你可以先这么找和安装：

```bash
openclaw skills search "summarize"
openclaw skills install summarize
```

真正好用的方式不是单纯说“帮我总结一下”，而是把总结目标讲清楚。比如：

- 总结成 5 个结论，面向技术负责人
- 只提炼对接入 API 有帮助的部分
- 帮我标出哪些内容值得我继续看原文

这样 `Summarize` 就不只是一个压缩工具，而会成为你做研究、做筛选、做输入分层时的第一道闸门。

## 4. Github：把开发流程从“看界面”变成“让 agent 帮你推进”

对开发者来说，`Github` 几乎必然会进第一批 skill。

因为它改变的不是信息来源，而是交互方式。你以前要自己打开 PR、切到 CI 页面、点开失败日志、回到 issue 列表，再去组织结论。接进 OpenClaw 以后，这些动作就能被压缩成一段任务描述。

安装建议同样是先搜再装：

```bash
openclaw skills search "github"
openclaw skills install github
```

它特别适合的几个用法是：

- 早上先看一遍昨晚失败的 CI，并按原因归类
- 汇总某个 PR 的 review 意见，整理成待办
- 看某个 issue 最近几天有没有新增讨论和阻塞点

更进一步一点，你可以把它和 `self-improving-agent` 配合起来。这样 OpenClaw 不只是知道 GitHub 上发生了什么，还会逐渐记住你平时更关心哪类失败、哪种 review 风格、以及你总结问题时偏好的结构。

[配图3](./assets/配图3-20260411-062518.png)

## 5. Weather：看起来最简单，却最容易变成组合工作流里的常驻能力

很多人第一次看到 `Weather` 会觉得它太基础了，甚至不像一个“值得进前五”的 skill。

但问题不在它单独能做什么，而在它和其他 skill 拼起来以后能不能变成日常入口。

`Weather` 的典型价值并不是“查今天多少度”，而是被塞进这种组合任务里：

- 给我一个上班前简报：天气、今天的会议、紧急邮件
- 如果下午要外出，顺手提醒我天气变化
- 当天有客户拜访时，把天气、交通和时间安排一起整理

安装时建议先搜：

```bash
openclaw skills search "weather"
openclaw skills install weather
```

如果你只单独用它查天气，它当然不算惊艳。但一旦你把它接进早间 brief、出门提醒或日程预处理里，它很容易变成你每天都会触发的一段固定能力。

## 这 5 个 skill，应该按什么顺序装？

如果你是第一次认真配 OpenClaw，我建议顺序是：

1. `Summarize`
2. `Gog`
3. `Github`
4. `Weather`
5. `self-improving-agent`

这不是热度顺序，而是“最快产生体感”的顺序。

原因也很简单：

- `Summarize` 最容易立刻感受到效率收益
- `Gog` 最容易把日常办公动作串起来
- `Github` 对开发者的日常价值极高
- `Weather` 适合补成组合式简报
- `self-improving-agent` 的收益最大，但它通常需要一点时间积累

如果你本身就是重度开发者，也可以把 `Github` 提到第二个。  
如果你每天都在邮件、会议、文档之间来回切，`Gog` 完全可以排第一。

## 真正值得记住的不是“装哪 5 个”，而是“先装哪一类能力”

回头看这 5 个 skill，会发现它们其实代表了 5 类完全不同的能力层：

- 长期偏好沉淀：`self-improving-agent`
- 工作套件联动：`Gog`
- 信息压缩：`Summarize`
- 开发流程接入：`Github`
- 环境信息补全：`Weather`

这也是为什么它们比很多“看起来更炫”的 skill 更值得先装。

因为一套好用的 OpenClaw，不是靠少数高光 demo 组成的，而是靠这些每天都能接管动作的基础能力叠出来的。

[配图4](./assets/配图4-20260411-062518.png)

如果你现在正准备配第一台真正会干活的 OpenClaw，我会建议你从这 5 个开始。

先别急着追求装得多，先让它稳定接住你每天都会做的那几件事。等这套动作跑顺了，你再往上叠更细分的 skill，收益会大很多。

最后一句判断：

如果你是 OpenClaw 新手，这 5 个 skill 值得现在就装。  
如果你已经装了一堆 skill 但觉得“没形成工作流”，更应该回头检查自己是不是缺了这 5 类基础能力。

## 延伸阅读

- OpenClaw CLI 安装技能说明：<https://docs.openclaw.ai/de/cli/index>
- OpenClaw Hub 热门技能与下载数据：<https://openclaw-hub.org/>
- 社区装机交叉筛选文章：<https://rentamac.io/best-openclaw-skills/>
