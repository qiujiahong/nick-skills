# Reusable prompt: switch OpenAI Codex account in OpenClaw

Use this as the default reusable prompt when the user wants to switch to another OpenAI Codex account on an OpenClaw server.

```text
请帮我在这台 OpenClaw 服务器上重新配置一个新的 OpenAI Codex 账号，并确保 openai-codex/gpt-5.4 可正常使用。

目标：
1. 用新的 ChatGPT 账号重新做 openai-codex OAuth 登录
2. 确保 OpenClaw Gateway 走 Clash 代理
3. 确保 openai-codex/gpt-5.4 已注册到模型列表
4. 确保切换到 openai-codex/gpt-5.4 后能正常回复，不超时
5. 如有必要，重启 gateway / clash 使配置生效
6. 最后汇总是否成功、当前模型、改动文件、以后最少重做哪几步

已知环境：
- Linux 服务器
- Clash Meta 已安装
- HTTP 代理端口：127.0.0.1:7890
- OpenClaw Gateway systemd user service 文件：~/.config/systemd/user/openclaw-gateway.service
- Clash 目录：/etc/clash
- Clash service：/etc/systemd/system/clash-meta.service

执行要求：
- 先检查 Clash 是否运行、是否 global、GLOBAL 是否是美国节点、代理出口是否为美国
- 检查 gateway service 是否包含 HTTP_PROXY / HTTPS_PROXY / no_proxy / NODE_OPTIONS=--use-env-proxy
- 不要使用 global-agent/bootstrap，优先使用 Node 原生 --use-env-proxy
- 用下面命令启动 OAuth：
  HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 node --use-env-proxy /usr/local/nodejs/lib/node_modules/openclaw/dist/index.js models auth login --provider openai-codex
- 把 OAuth URL 发给我，等我登录后，把我发回的 callback URL 粘贴回终端
- 检查 ~/.openclaw/agents/assistant/agent/auth-profiles.json 是否更新
- 检查 ~/.openclaw/openclaw.json 中 agents.defaults.models 是否有 openai-codex/gpt-5.4
- 如果配置有改动，重启 gateway 并确认进程环境变量生效
- 最后必须实际切到 openai-codex/gpt-5.4 并完成一次正常回复，不能只停留在“切换成功”

输出格式：
1. 是否成功
2. 当前账号是否已替换
3. 当前模型是否能正常使用 openai-codex/gpt-5.4
4. 改动了哪些文件
5. 如果以后 OpenClaw 升级导致配置丢失，最少需要重做哪几步
```

## Short version

```text
请帮我把这台 OpenClaw 服务器的 OpenAI Codex 账号切换成新账号，并确保 openai-codex/gpt-5.4 真正可用。

要求：
- 先确认 Clash 是 global 且出口为美国
- 检查 gateway service 是否使用 HTTP_PROXY/HTTPS_PROXY 和 NODE_OPTIONS=--use-env-proxy
- 用 Node 原生命令发起 openai-codex OAuth 登录
- 我登录后把 callback URL 发给你，你负责粘贴回终端
- 检查 auth-profiles.json 和 openclaw.json 是否更新
- 如有改动就重启 gateway
- 最后必须实际测试 openai-codex/gpt-5.4 回复成功，再算完成
```
