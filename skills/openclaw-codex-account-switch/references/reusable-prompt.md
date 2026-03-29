# Reusable Prompts: OpenClaw Codex Account Switch

## 长版（完整执行提示词）

```
请帮我切换 OpenClaw 服务器上的 OpenAI Codex 账号，按以下步骤执行：

1. 检查代理：确认 Clash 运行中、模式为 global、节点为美国。执行 curl -x http://127.0.0.1:7890 https://ipinfo.io/json 确认出口为 US。

2. 检查 Gateway 配置：查看 ~/.config/systemd/user/openclaw-gateway.service，确保有 http_proxy/https_proxy/HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7890，NODE_OPTIONS=--use-env-proxy，no_proxy 包含内网段。不要用 global-agent/bootstrap。

3. 执行 OAuth 登录：
   HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 node --use-env-proxy /usr/local/nodejs/lib/node_modules/openclaw/dist/index.js models auth login --provider openai-codex
   把 OAuth URL 发给我，我在浏览器登录后把 callback URL 发回来。

4. 登录后校验：检查 ~/.openclaw/agents/assistant/agent/auth-profiles.json 中 openai-codex:default 存在且 token 已更新；检查 ~/.openclaw/openclaw.json 中 openai-codex/gpt-5.4 已注册。

5. 端到端验收：切换到 openai-codex/gpt-5.4，发一条测试消息，确认模型正常回复。仅 OAuth 成功不算完成。

6. 如果遇到问题：
   - gateway 起不来 → 检查是否误用了 global-agent/bootstrap
   - 模型超时 → 检查 gateway 进程环境变量、出口 IP、是否重启过、账号配额
```

## 短版（快速 checklist）

```
切换 Codex 账号 checklist：
1. curl -x http://127.0.0.1:7890 https://ipinfo.io/json → 确认 US
2. 确认 gateway service 有 NODE_OPTIONS=--use-env-proxy（非 global-agent）
3. HTTPS_PROXY=http://127.0.0.1:7890 node --use-env-proxy .../openclaw/dist/index.js models auth login --provider openai-codex
4. 拿到 OAuth URL → 用户浏览器登录 → callback URL 粘回终端
5. 检查 auth-profiles.json + openclaw.json
6. 切到 openai-codex/gpt-5.4 发测试消息 → 收到回复才算完成
```
