---
name: openclaw-team-setup
description: Create or repair an OpenClaw multi-agent team for a project, including isolated agents, role prompts, subagent and ACP wiring, channel routing, backups, validation, and restart. Use when setting up pm/dev/qa style teams, migrating main into a backup role, or connecting Feishu/Lark bots without embedding secrets into the skill.
---

# OpenClaw Team Setup

Use this skill when a project needs a repeatable way to configure an OpenClaw multi-agent team such as `pm / dev / qa`.

This skill is for **project-level setup and repair**, not day-to-day chat use.

## What This Skill Does

- Backs up current OpenClaw config before changes
- Creates or updates isolated agents
- Writes project-specific role prompts into each agent workspace
- Configures `subagents` and ACP runtime wiring
- Configures channel routing, especially Feishu/Lark
- Validates config, restarts the gateway, and defines test steps

## Do Not Store Secrets In This Skill

Never hardcode the following into skill files:

- gateway token
- app id / app secret
- API keys
- OAuth tokens
- allowlists with private user ids unless the user explicitly wants them persisted

During execution, ask the user to provide sensitive values or tell you where they already live.
Prefer writing placeholders into documentation and writing real secrets only into the runtime config the user explicitly wants updated.

## Inputs To Collect At Runtime

Before editing config, gather only the minimum required values:

- target team roles, for example `pm / dev / qa`
- which agent should stay `default`
- which roles should use OpenClaw native subagents
- which roles should use ACP, for example Codex
- target model ids
- target workspace paths if they should differ from defaults
- channel integration choice, for example Feishu
- per-channel account ids used for routing, for example `pm`, `dev`, `qa`
- any app credentials or tokens the user wants persisted

If the user does not provide a value, leave a placeholder in docs and stop short of inventing secrets.

## Default Workflow

### 1. Inspect Current State

Check:

- `~/.openclaw/openclaw.json`
- existing agents in `agents.list[]`
- existing agent workspaces
- existing agent auth/model stores
- plugin status for ACP backends and channels
- current bindings

Confirm whether the current default agent should remain the default.

### 2. Backup Before Changes

Before any config rewrite:

- create a dated backup directory or archive
- include `~/.openclaw/`
- include launch agent or service files when relevant
- include any project-owned team prompt files that informed the setup

Record the backup path in the final summary.

### 3. Create Or Update Agent Topology

Typical pattern:

- keep `main` as backup or personal entry
- create a dedicated `pm`
- create isolated `dev`
- create isolated `qa`

For each agent, set:

- `id`
- `workspace`
- `agentDir`
- `model`
- optional `identity`
- optional `runtime` for ACP roles
- optional `subagents.allowAgents`

Do not assume `main` must be the project manager.

### 4. Write Role Prompts Into Workspaces

Put the project-specific role prompt into each workspace `AGENTS.md`.

Keep each role file focused:

- `pm`: orchestration, decomposition, delivery summary
- `dev`: implementation, code changes, self-test, risk notes
- `qa`: test design, validation, defect framing, risk assessment

Do not copy long generic bootstrap text unless the project explicitly wants it.

### 5. Configure Subagents And ACP

Use OpenClaw native subagents for roles such as `qa` when the role should be spawned via `sessions_spawn`.

Use ACP runtime for roles such as `dev` when the role should run an external harness such as Codex.

Recommended patterns:

- `pm.subagents.allowAgents: ["qa"]`
- `dev.runtime.type: "acp"`
- `dev.runtime.acp.agent: "codex"`
- `dev.runtime.acp.backend: "acpx"`

If ACP is used, also check:

- `acp.enabled`
- `acp.defaultAgent`
- `acp.allowedAgents`
- ACP backend plugin status

For `acpx`, the common non-interactive setting is:

- `permissionMode: approve-all`
- `nonInteractivePermissions: fail`

### 6. Configure Channel Routing

If the team is exposed through channels, bind each account or route target to the intended agent.

Example pattern:

- `pm <- feishu accountId=pm`
- `dev <- feishu accountId=dev`
- `qa <- feishu accountId=qa`

Do not rely on naming alone. Confirm that actual routing bindings exist.

For Feishu-specific guidance, read [references/feishu.md](references/feishu.md).

### 7. Validate And Restart

Always run:

- config validation
- agent listing
- binding listing
- plugin inspection for ACP or channel plugins you changed
- gateway restart
- gateway status

If routing still appears wrong, inspect gateway logs for lines like:

- `feishu[dev]: dispatching to agent (session=agent:main:main)`

That usually means the gateway is still using old bindings or a wrong default route.

### 8. Produce Test Instructions

After setup, generate minimal end-to-end tests for:

- role routing
- `pm -> qa`
- `pm -> dev`
- full `pm -> dev + qa`

Keep the test instructions in a project markdown file when useful.

## Editing Rules

- Use `apply_patch` for direct file edits
- Prefer one final config write over multiple concurrent config mutations
- Avoid parallel writes to `openclaw.json`; they can overwrite each other
- If you must use CLI helpers like `openclaw agents bind`, re-read the config afterward to confirm nothing was lost

## Common Failure Modes

### All messages still go to `main`

Usually means one of:

- no routing bindings
- bindings exist in config but gateway was not restarted
- bindings were overwritten by concurrent writes

### Channel account is recognized but dispatch still goes to `main`

Check gateway logs. If you see:

- `feishu[pm] ... dispatching to agent (session=agent:main:main)`

then the live gateway is not honoring the expected route yet.

### ACP role exists but does not execute

Check:

- ACP plugin enabled
- ACP backend loaded
- ACP allowed agents configured
- runtime block exists on the intended agent

### Skill-safe handling of secrets

If a secret is missing:

- stop writing placeholders into config if they would break a running deployment
- ask the user for the value or tell them exactly which config key to populate
- keep the skill documentation generic and secret-free

## Minimal Output Summary

At the end of execution, report:

- backup path
- changed config files
- created or updated agents
- channel routing status
- ACP / subagent status
- exact tests the user should run next
