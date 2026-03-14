---
name: openclaw-codex-account-switch
description: Reconfigure or switch the OpenAI Codex account used by OpenClaw on a Linux server, including proxy checks, OAuth login, model registration, gateway restart, and end-to-end validation of openai-codex/gpt-5.4. Use when the user wants to change Codex accounts, re-login, fix Codex auth after expiry, re-enable GPT-5.4, or create a reusable prompt/checklist for this workflow.
---

# OpenClaw Codex Account Switch

Reconfigure OpenClaw to use a different OpenAI Codex account and verify that `openai-codex/gpt-5.4` really works.

## Core workflow

1. Verify proxy path first.
2. Verify OpenClaw gateway proxy settings.
3. Start Codex OAuth login.
4. Wait for the user to complete browser login and paste the callback URL.
5. Finish auth and verify `auth-profiles.json` changed.
6. Ensure `openai-codex/gpt-5.4` is registered in `~/.openclaw/openclaw.json`.
7. Restart gateway if config changed.
8. Test actual model response, not just model selection.

Do not declare success until the model has produced a normal reply.

## Proxy requirements

Before login or testing, confirm:

- Clash is running.
- Clash mode is `global`.
- Global node is a US node.
- Proxy egress is US.

Useful checks:

```bash
curl -s -X PATCH http://127.0.0.1:9090/configs -d '{"mode":"global"}'
curl -s http://127.0.0.1:9090/proxies/GLOBAL
curl -s -x http://127.0.0.1:7890 https://ipinfo.io/json
```

If the global node is wrong, switch it before continuing.

## Gateway requirements

Check `~/.config/systemd/user/openclaw-gateway.service`.

Preferred proxy settings:

```ini
Environment=http_proxy=http://127.0.0.1:7890
Environment=https_proxy=http://127.0.0.1:7890
Environment=HTTP_PROXY=http://127.0.0.1:7890
Environment=HTTPS_PROXY=http://127.0.0.1:7890
Environment=no_proxy=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
Environment="NODE_OPTIONS=--use-env-proxy"
```

Use Node's native `--use-env-proxy`.
Do **not** use `global-agent/bootstrap` unless the host clearly has that package wired correctly.

If the service file changes, reload and restart:

```bash
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
systemctl --user is-active openclaw-gateway
```

## OAuth login flow

Prefer this command over noisy `proxychains` runs:

```bash
HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 node --use-env-proxy /usr/local/nodejs/lib/node_modules/openclaw/dist/index.js models auth login --provider openai-codex
```

After the tool prints the OAuth URL:

1. Send the URL to the user.
2. Tell the user to open it in a local browser.
3. Tell the user to log into the intended ChatGPT account.
4. Ask the user to paste back the full `http://localhost:1455/auth/callback?...` URL.
5. Paste that URL back into the waiting terminal session.

Successful output should include:

- `Auth profile: openai-codex:default`
- `Default model available: openai-codex/gpt-5.4`

## Verification after login

Check:

- `~/.openclaw/agents/assistant/agent/auth-profiles.json`
- `~/.openclaw/openclaw.json`

Confirm that:

- `openai-codex:default` exists and is `oauth`
- expiry/token fields changed after re-login
- `openai-codex/gpt-5.4` exists in `agents.defaults.models`

If missing in `openclaw.json`, add it and restart the gateway.

## Validation standard

Use this order:

1. Confirm the model is allowed.
2. Switch to `openai-codex/gpt-5.4`.
3. Send a simple test message.
4. Confirm the assistant replies normally.

Passing OAuth alone is **not** enough.
Passing model switch alone is **not** enough.
A real response is the acceptance test.

## Troubleshooting

### `NODE_OPTIONS=--require global-agent/bootstrap` breaks startup

Likely cause: the preload module is not installed in a resolvable path for the gateway runtime.

Preferred fix: replace it with:

```ini
Environment="NODE_OPTIONS=--use-env-proxy"
```

### OAuth succeeds but GPT-5.4 times out

Check, in order:

1. Gateway process environment really contains `NODE_OPTIONS=--use-env-proxy`
2. Gateway process environment still contains `HTTP_PROXY` and `HTTPS_PROXY`
3. Proxy egress is US
4. Gateway was restarted after config edits
5. The account has usable Codex quota

### `proxychains` output is too noisy

Prefer the native Node proxy method above.
Only fall back to `proxychains4` if the native path fails.

## Reusable prompt

If the user asks for a reusable prompt or checklist, read `references/reusable-prompt.md` and adapt it instead of rewriting from scratch.
