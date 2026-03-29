---
name: openclaw-agent-provisioning
description: "创建或修复 OpenClaw agent，并绑定指定的 Feishu/Lark 机器人。支持普通 OpenClaw agent 与 ACP agent，两者流程严格区分。适用于：新建 agent、补绑飞书机器人、修复 bindings、校验 status --deep、判断是否还需要 pairing / approve。"
---

# OpenClaw Agent Provisioning

把“创建 agent + 绑定 Feishu 机器人 + 校验状态”封装成稳定流程。

这个 skill 面向 **执行配置变更的 agent**，不是给终端用户看的介绍文档。

## 1. 适用场景

当用户有以下诉求时使用本 skill：

- 新建一个 **普通 OpenClaw agent** 并绑定一个新的 Feishu 机器人
- 新建一个 **ACP agent** 并绑定一个新的 Feishu 机器人
- agent 已存在，只补 channel account 与 binding
- 修复 Feishu `accountId -> agentId` 路由
- 改完后要求跑 `openclaw status --deep` 验证
- 需要明确判断是否还要执行 pairing / approve

## 2. 最关键的分流规则

先判断用户要的是哪一种：

### A. 普通 OpenClaw agent

如果用户说的是：
- “创建一个普通 OpenClaw agent”
- “不是 ACP agent”
- “新建 agent 并绑定飞书机器人”
- 只是提到 agent / Feishu / account / binding，没有明确说 ACP

默认按 **普通 OpenClaw agent** 处理。

### B. ACP agent

只有用户明确说以下之一，才走 ACP：
- ACP agent
- Codex / Claude / Pi / OpenCode / Gemini / Kimi 作为 agent runtime
- 要配置 `runtime.type: acp`
- 要创建 ACP 专用 agent

**不要把普通 agent 创建误走成 ACP。**

## 3. 输入参数

### 普通 agent 最少需要

- `agent id`
- `app id`
- `app secret`

建议同时收集：

- `agent name`
- `workspace`
- `agentDir`
- `accountId`
- `botName`

### ACP agent 额外需要

在上面的基础上，再确认：

- ACP runtime agent（例如 `codex` / `claude` / `pi`）
- ACP backend（通常 `acpx`）
- ACP mode（如适用）
- runtime cwd（如适用）

### 默认值约定

如果用户没单独指定，常用默认可按以下推导：

- `accountId = agent id`
- `agent name = agent id`
- `workspace = /Users/jgdt/.openclaw/workspace-<agent_id>`
- `agentDir = /Users/jgdt/.openclaw/agents/<agent_id>/agent`
- `botName` 由用户提供；没有就提示用户补充，避免乱起名

## 4. 修改原则

### 只改指定对象

执行时必须遵守：

- 只新增或更新当前指定的 `channels.feishu.accounts.<accountId>`
- 只新增或更新当前指定的 `binding`
- 不要碰其他已有机器人账号
- 不要顺手重排或清洗整个 `openclaw.json`
- 不要擅自把别的 agent 改成 ACP
- 不要把已有 ACP agent 改回普通 agent

### Secret 处理

不要把真实 secret 写进 skill 文档本身。

真实的 `appId / appSecret` 只允许在执行时写入用户明确指定的运行配置：
- `~/.openclaw/openclaw.json`

## 5. 推荐执行顺序

## Step 1: 检查当前状态

优先检查：

- `~/.openclaw/openclaw.json`
- `agents.list[]`
- `bindings`
- `channels.feishu.accounts`

确认：

- agent 是否已存在
- accountId 是否已存在
- binding 是否已存在
- 是否已经是错误绑定

## Step 2: 创建或更新 agent

### 普通 OpenClaw agent

优先使用 OpenClaw CLI：

```bash
openclaw agents add <agent_id> \
  --workspace <workspace> \
  --agent-dir <agentDir> \
  --non-interactive
```

如果 agent 已存在：
- 不重复创建
- 继续处理 Feishu account 与 binding

### ACP agent

ACP agent 需要在 agent 配置中显式写入 runtime 块，例如：

```json
{
  "runtime": {
    "type": "acp",
    "acp": {
      "agent": "codex",
      "backend": "acpx"
    }
  }
}
```

规则：
- 普通 agent 不要写 ACP runtime
- ACP agent 要清楚写明 runtime 类型与目标 harness
- 如果用户只是要“普通 agent + Feishu”，不要擅自加 ACP runtime

## Step 3: 增加 Feishu account

在 `~/.openclaw/openclaw.json` 中增加或更新：

```json
channels.feishu.accounts.<accountId>
```

典型结构：

```json
{
  "appId": "<app_id>",
  "appSecret": "<app_secret>",
  "botName": "<bot_name>"
}
```

注意：
- 只改当前 `accountId`
- 不要覆盖 `channels.feishu.accounts` 整体
- 不要删默认账号或其他命名账号

## Step 4: 增加 binding

需要有明确路由：

```json
{
  "agentId": "<agent_id>",
  "match": {
    "channel": "feishu",
    "accountId": "<accountId>"
  }
}
```

可以用 CLI：

```bash
openclaw agents bind --agent <agent_id> --bind feishu:<accountId>
```

但执行后要重新检查配置，确认没有丢字段或误写。

如果 binding 已存在但 agent 指错：
- 修复成指定 `agentId`
- 不要保留重复冲突 binding

## Step 5: 校验

至少执行：

```bash
openclaw status --deep
```

建议同时检查：

```bash
openclaw agents list
openclaw agents bindings
openclaw config validate
```

对 Feishu 重点确认：
- 该账号已出现在 Feishu health/status 中
- 目标账号状态是 `ok`，或至少返回明确的待处理原因

## Step 6: 判断是否还需要 pairing / approve

如果状态里显示：
- 需要配对
- 需要 approve
- 需要人工完成授权

必须在最终回复中直接告诉用户：
- 还缺哪一步
- 要执行什么命令
- 或者要去哪里完成操作

如果命令可确定，就直接给准确命令，不要只说“你再配一下”。

## 6. 输出格式要求

最终汇报至少包含：

- 这是 **普通 agent** 还是 **ACP agent**
- agent 是新建还是复用已有
- 新增或更新了哪个 `accountId`
- 新增或更新了哪个 binding
- `openclaw status --deep` 的关键结果
- Feishu 该账号是否 `ok`
- 是否还需要 pairing / approve
- 如果需要，给出准确下一步命令或操作

## 7. 常见坑

### 坑 1：把普通 agent 误配成 ACP

这是最常见错误之一。

修正规则：
- 用户没明确说 ACP，就按普通 agent 处理
- 不要因为用户提到 Codex/OpenClaw 就自动写 `runtime.type: acp`

### 坑 2：只创建了 agent，没有创建 Feishu account

创建 agent 不等于渠道可用。

还必须确认：
- `channels.feishu.accounts.<accountId>` 存在
- `bindings` 存在

### 坑 3：只写了 Feishu account，没有写 binding

没有 binding 时，消息可能继续走默认路由或走错 agent。

### 坑 4：修改了 config，但没做状态验证

配置写完不代表生效。

至少要跑：

```bash
openclaw status --deep
```

### 坑 5：改动时影响了其他机器人

必须做精准修改：
- 只改指定账号
- 不重写其他账号
- 不因为一次新增就“顺手整理”整个 channel 配置

## 8. 可复用中文工单模板

当用户只是给一句模糊需求时，可以引导对方使用这个模板：

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

要求：
1. 如果 agent 不存在，就创建 agent
2. 只新增这个飞书账号，不改其他已有机器人
3. 在 ~/.openclaw/openclaw.json 里新增 channels.feishu.accounts.<accountId>
4. 新增 binding：feishu accountId=<accountId> -> agentId=<agent_id>
5. 配完后检查 openclaw status --deep
6. 确认 Feishu 健康状态里该账号是否 ok
7. 如果需要 pairing / approve，直接告诉我下一步命令
8. 如果是普通 agent，不要走 ACP；只有我明确说 ACP 时才走 ACP
```

## 9. 简短版工单模板

```text
帮我创建一个 OpenClaw agent 并绑定飞书机器人。
- agent type: 普通 | ACP
- agent id: <agent_id>
- app id: <app_id>
- app secret: <app_secret>
- bot name: <bot_name>

要求：
- 新建 agent（如不存在）
- 绑定 Feishu account 到同名 agent
- 只改指定账号，别动其他机器人
- 最后检查状态并告诉我是否还需要 pairing / approve
- 如果没明确说 ACP，就按普通 agent 处理
```
