# 项目级 Skill：`openclaw-team-setup`

这篇文章总结了项目级 skill `openclaw-team-setup` 的用途、适用场景和使用方式。

这个 skill 的目标不是“帮你聊业务”，而是把 **OpenClaw 多智能体团队的配置过程标准化**，让后续配置 `pm / dev / qa`、接入 ACP、接入飞书机器人、做路由与验证时，不需要每次从零整理流程。

## 这个 Skill 解决什么问题

在 OpenClaw 里配置多人团队，通常会同时碰到几类问题：

- 要不要保留 `main`
- `pm` 是不是独立 agent
- `dev` 用 ACP 还是原生 sub-agent
- `qa` 如何作为 sub-agent 被 `pm` 调用
- 飞书多个机器人怎么分别命中不同 agent
- 改完配置后为什么消息还是全到 `main`

`openclaw-team-setup` 的作用，就是把这些步骤收敛成一个固定流程：

1. 检查当前状态
2. 先做备份
3. 创建或更新 agent 拓扑
4. 写角色提示词
5. 配置 subagents / ACP
6. 配置飞书等渠道路由
7. 校验、重启、联调

## 安全处理方式

这个 skill **不会直接保存真实敏感信息**。

也就是说，skill 里不会写死：

- Gateway token
- 飞书 App ID / App Secret
- API key
- OAuth token

skill 的设计是：

- 在执行过程中提示操作者补充这些值
- 文档里只保留占位结构
- 真正写入运行配置时，才使用用户提供的值

这比把密钥直接烙进 skill 文件要安全得多，也更适合项目复用。

## Skill 里包含什么

当前这个 skill 包含两部分：

- [`skills/openclaw-team-setup/SKILL.md`](/Users/nick/Desktop/code/openclaw-share/mi/skills/openclaw-team-setup/SKILL.md)
- [`skills/openclaw-team-setup/references/feishu.md`](/Users/nick/Desktop/code/openclaw-share/mi/skills/openclaw-team-setup/references/feishu.md)

其中：

- `SKILL.md` 负责定义整个项目级配置流程
- `references/feishu.md` 专门补充飞书机器人接入、配对、路由和排错方法

## 适合怎么用

这个 skill 适合以下场景：

- 新项目第一次搭 OpenClaw 多智能体团队
- 现有配置混乱，需要重构为 `main / pm / dev / qa`
- 需要把 `dev` 切到 ACP + Codex
- 需要给 `pm / dev / qa` 分别挂飞书机器人
- 改了配置但路由异常，需要标准化排查

## 推荐的调用方式

如果后续你要用这个 skill，可以给 Codex 类似这样的任务：

```text
使用 openclaw-team-setup skill。
目标：
1. 保留 main 作为默认备份入口
2. 新建独立 pm
3. dev 使用 ACP + Codex
4. qa 使用 sub-agent
5. 接入飞书三个机器人，分别命中 pm/dev/qa
6. 所有敏感信息由我在过程中补充
7. 最后输出联调测试步骤
```

如果只想修复飞书路由问题，也可以缩小范围：

```text
使用 openclaw-team-setup skill，只处理 Feishu 路由修复。
不要改 agent 拓扑。
需要我补充的敏感信息请单独列出。
```

## 飞书部分为什么单独写参考文件

飞书接入里最容易出错的不是创建机器人本身，而是：

- 账号 id 和绑定的 `accountId` 不一致
- 配了多个机器人，但没有真正写 routing bindings
- 配置文件改了，网关没重启
- 网关还在按旧路由把所有消息派发到 `main`

所以把飞书相关注意点单独放进参考文件，比把它们混进主 skill 更实用，也更容易按需加载。

## 这个 Skill 的价值

这个 skill 的核心价值不是“多写了一份说明”，而是把一套容易反复出错的操作流程，收敛成一份 **可重复执行、可验证、对敏感信息友好** 的项目级能力。

以后如果你继续扩展团队，比如加：

- `ops`
- `reviewer`
- `research`

也可以沿着这个 skill 的同一套结构继续扩展，而不是重新摸索。

## 下一步建议

如果你希望这套 skill 更完整，下一步最值得补的是两件事：

- 增加一个 `references/testing.md`，专门放多智能体联调脚本
- 再补一个更短的“生产模式执行模板”，让调用 skill 时输入更少、输出更稳
