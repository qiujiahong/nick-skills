# Agent Provisioning

`agent-provisioning` 用来封装一个非常高频、也很容易踩坑的运维动作：

- 创建一个 **普通 OpenClaw agent** 或 **ACP agent**
- 绑定一个新的 **Feishu / Lark 机器人**
- 只修改指定账号和指定 binding
- 最后做 `openclaw status --deep` 验证
- 明确告诉操作者是否还需要 pairing / approve

这个 skill 的重点不是“怎么聊天”，而是把一套容易重复出错的配置流程变成一个稳定 SOP。

## 解决的问题

在日常配置里，这类请求经常长这样：

- “帮我创建一个 agent，再绑一个新的飞书机器人”
- “这是普通 agent，不是 ACP agent”
- “如果 agent 已存在，就只补 account 和 binding”
- “别改其他已有机器人”
- “最后帮我看 Feishu 状态是不是 ok”

听起来不复杂，但实际很容易出错：

- 把普通 agent 误做成 ACP
- 只创建了 agent，忘了加 Feishu account
- 加了 Feishu account，忘了写 binding
- 覆盖了其他已存在机器人配置
- 配完不跑状态检查，不知道到底有没有生效

这个 skill 的价值，就是把这些步骤标准化。

## 这个 skill 的边界

它主要处理：

- 单个 agent 的创建或复用
- 单个 Feishu account 的新增或更新
- 单个 `feishu:<accountId> -> <agentId>` binding 的新增或修复
- 普通 agent 与 ACP agent 的分流判断
- 最终状态校验与操作反馈

它**不负责**：

- 一次性设计整套 `pm/dev/qa` 团队拓扑
- 大规模重构整个 `openclaw.json`
- 替用户发明 secret、botName 或 runtime 方案

如果是项目级多智能体搭建，优先用 `openclaw-team-setup`。

## 普通 agent 与 ACP agent 的规则

这是这个 skill 最重要的部分：

- **默认按普通 OpenClaw agent 处理**
- 只有用户明确说了 `ACP`，才走 ACP agent 流程

也就是说：

- “帮我创建 agent 并绑定飞书机器人” → 默认普通 agent
- “帮我创建 ACP agent，用 Codex” → 明确 ACP

这个分流规则应该始终保持保守，避免误配。

## 推荐输入模板

### 完整版

```text
请帮我新建一个 OpenClaw agent，并绑定一个新的飞书机器人。
信息如下：
- agent type: 普通 | ACP
- agent id: <agent_id>
- agent name: <agent_name>
- workspace: /Users/jgdt/.openclaw/workspace-<agent_id>
- agentDir: /Users/jgdt/.openclaw/agents/<agent_id>/agent
- accountId: <account_id>
- App ID: <app_id>
- App Secret: <app_secret>
- botName: <bot_name>

如果是 ACP agent，再补充：
- runtime agent: <codex|claude|pi|opencode|gemini|kimi>
- backend: <acpx>
- cwd: <path, optional>
```

### 极简版

```text
帮我创建一个 OpenClaw agent 并绑定飞书机器人。
- agent type: 普通 | ACP
- agent id: <agent_id>
- app id: <app_id>
- app secret: <app_secret>
- bot name: <bot_name>
```

## 执行要求

这个 skill 会强调以下要求：

1. agent 不存在就创建
2. agent 已存在就复用，不重复造轮子
3. 只改指定的 Feishu account
4. 只改指定的 binding
5. 不碰其他机器人账号
6. 结束前必须跑状态检查
7. 如果还需要 pairing / approve，要明确告诉用户下一步

## 和其他 skill 的关系

- **项目级多智能体拓扑**：用 `openclaw-team-setup`
- **Codex OAuth 账号切换**：用 `openclaw-codex-account-switch`
- **单 agent 创建 + Feishu 绑定**：用 `openclaw-agent-provisioning`

## 为什么值得单独做成 skill

因为这件事看着像“顺手配置一下”，实际上有稳定的输入、输出和校验步骤，非常适合沉淀成 SOP。

单独做成 skill 以后，后续你只要贴参数，就可以直接复用，而不用每次重新解释：

- 是普通 agent 还是 ACP
- 要不要创建 agent
- 要不要补 Feishu account
- 要不要补 binding
- 最后要不要看 `status --deep`

这会比每次口头描述稳很多。
