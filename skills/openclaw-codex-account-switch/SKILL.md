---
name: openclaw-codex-account-switch
description: "切换/重配 OpenClaw 服务器上的 OpenAI Codex 账号。触发场景：切换 Codex 账号、重登 OpenAI Codex、修复 Codex OAuth、配置 GPT-5.4、OpenClaw Codex account switch、Codex re-login、reconfigure openai-codex、排查 Codex 登录成功但模型超时。"
---

# OpenClaw Codex Account Switch

为 OpenClaw 服务器切换/重配 OpenAI Codex (openai-codex) 账号的完整操作流程。面向 agent 执行，非用户文档。

## 1. Core Workflow

```
检查代理 → 配置 Gateway → OAuth 登录 → 登录后校验 → 端到端验收
```

**关键原则：OAuth 成功 ≠ 完成。必须端到端发消息验证模型回复才算成功。**

## 2. Proxy Requirements

执行前必须确认：

```bash
# 1. Clash 运行中
systemctl --user status clash-meta 2>/dev/null || systemctl status clash-meta

# 2. Clash 模式为 global，GLOBAL 节点为美国
# 通过 Clash Dashboard 或 API 确认

# 3. 验证出口是美国
curl -x http://127.0.0.1:7890 https://ipinfo.io/json
# 确认 "country": "US"
```

**如果出口不是美国，停止后续操作，先修代理。**

## 3. Gateway Proxy Configuration

检查 `~/.config/systemd/user/openclaw-gateway.service`，确保包含：

```ini
Environment=http_proxy=http://127.0.0.1:7890
Environment=https_proxy=http://127.0.0.1:7890
Environment=HTTP_PROXY=http://127.0.0.1:7890
Environment=HTTPS_PROXY=http://127.0.0.1:7890
Environment=no_proxy=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
Environment="NODE_OPTIONS=--use-env-proxy"
```

**重点：**
- ✅ 使用 Node 原生 `--use-env-proxy`
- ❌ 不要用 `global-agent/bootstrap`（会导致模块路径不可解析、gateway 起不来）

修改后必须重载并重启：

```bash
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
# 或
openclaw gateway restart
```

## 4. OAuth Login Flow

使用以下命令发起登录（不要用 proxychains）：

```bash
HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
  node --use-env-proxy /usr/local/nodejs/lib/node_modules/openclaw/dist/index.js \
  models auth login --provider openai-codex
```

流程步骤：

1. 命令输出 OAuth URL
2. **把 URL 发给用户**（用户需在本地浏览器打开）
3. 用户在浏览器中登录目标 ChatGPT 账号
4. 浏览器会跳转到 `http://localhost:1455/auth/callback?...`（因为在服务器上，会失败）
5. **用户把完整的 callback URL 发回来**
6. 把 callback URL 粘贴回终端
7. 成功标志：
   - `Auth profile: openai-codex:default`
   - `Default model available: openai-codex/gpt-5.4`

## 5. Verification After Login

检查配置文件：

```bash
# 检查 auth profile
cat ~/.openclaw/agents/assistant/agent/auth-profiles.json | jq '.["openai-codex:default"]'

# 检查 openclaw.json 中模型注册
cat ~/.openclaw/openclaw.json | jq '.agents.defaults.models'
```

确认：
- `openai-codex:default` 存在
- 类型为 `oauth`
- `token` / `expires` 已更新
- `openai-codex/gpt-5.4` 在 `agents.defaults.models` 中已注册

## 6. Validation Standard（验收标准）

**必须完成全部三步才算成功：**

1. ✅ 切换到 `openai-codex/gpt-5.4`
2. ✅ 发一条简单测试消息（如 "hello, reply with one word"）
3. ✅ 模型正常回复

仅 OAuth 成功或仅切换成功都**不算完成**。

## 7. Troubleshooting

### 情况 A：global-agent/bootstrap 导致 gateway 起不来

**症状：** gateway 启动失败，日志含模块路径错误或 preload 失败

**修复：** 将 `NODE_OPTIONS` 从 `--require global-agent/bootstrap` 改为 `--use-env-proxy`

### 情况 B：OAuth 成功但 GPT-5.4 超时

排查顺序：

1. gateway 进程环境变量是否包含 `NODE_OPTIONS=--use-env-proxy`
   ```bash
   cat /proc/$(pgrep -f openclaw-gateway | head -1)/environ | tr '\0' '\n' | grep -i proxy
   ```
2. `HTTP_PROXY` / `HTTPS_PROXY` 是否设置正确
3. 出口是否仍是美国（`curl -x http://127.0.0.1:7890 https://ipinfo.io/json`）
4. gateway 是否在改配置后**重启过**
5. 目标账号是否有可用 Codex 配额

### 情况 C：proxychains 输出噪音太大

- 首选 `node --use-env-proxy` + 环境变量
- `proxychains4` 仅作为最后备选

## 8. Reusable Prompt

详见 [references/reusable-prompt.md](references/reusable-prompt.md)，包含长版和短版可复用提示词。
