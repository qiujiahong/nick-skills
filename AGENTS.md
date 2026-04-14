# AGENTS.md - nick-skills

This repository is the development home for reusable OpenClaw / Codex skills.

## Session Startup

Before changing files in this repo:

1. Run `git status --short --branch`.
2. Read this file and the root `README.md`.
3. Read the relevant `skills/<skill-name>/SKILL.md` before editing that skill.
4. If workspace memory files exist (`SOUL.md`, `USER.md`, `MEMORY.md`, `memory/YYYY-MM-DD.md`), read them in direct main-session chats.

Use `rg` / `rg --files` for searching. Keep edits scoped to the requested skill or documentation.

## Repository Scope

Primary source lives under:

```text
skills/<skill-name>/
```

Each skill should keep its main instructions in `SKILL.md`. Optional implementation files should stay close to the skill:

```text
skills/<skill-name>/scripts/
skills/<skill-name>/references/
skills/<skill-name>/agents/
```

Generated outputs should not be committed unless they are deliberate examples or fixtures.

## Current Skills

The active skill set is:

- `ai-topic-research`
- `countryhuman-video-maker`
- `fin-ai-daily-brief`
- `image-gen`
- `tavily-search`
- `teaching-video-maker`
- `tech-blog-writer`
- `video-gen`
- `voice-tts`
- `wechat-mp-publisher`

`agent-provisioning` has been removed. Do not recreate it unless the user explicitly asks for that skill again.

## Merge Ownership

When reconciling local work with `git@github.com:qiujiahong/nick-skills.git`, use these ownership rules unless the user gives a newer instruction:

- Keep local versions for `ai-topic-research`.
- Keep local versions for `countryhuman-video-maker`.
- Keep remote versions for `fin-ai-daily-brief`.
- Keep local versions for `image-gen`.
- Keep local versions for `tavily-search`.
- Keep local versions for `teaching-video-maker`.
- Keep local versions for `tech-blog-writer`.
- Keep local versions for `video-gen`.
- Keep local versions for `voice-tts`.
- Keep local versions for `wechat-mp-publisher`.
- Delete `agent-provisioning`.

Do not stage or revert unrelated local work. If an unrelated file is already dirty, leave it alone.

## Skill Authoring Rules

- Preserve the YAML front matter in each `SKILL.md`, especially `name` and `description`.
- Prefer scripts over large repeated command blocks when a workflow needs automation.
- Put reusable implementation in `scripts/` and explanatory source material in `references/`.
- Do not commit real secrets. Use `.env.example`, `.env.local.example`, or placeholder values.
- Keep local-only API credentials out of documentation and tests.
- If a skill depends on another skill in this repo, reference it by relative path and keep the dependency explicit.
- For user-facing automation that publishes externally, default to draft / preview behavior unless the user explicitly asks to publish.

## Verification

Choose checks based on the changed surface:

- Documentation-only edits: review rendered Markdown structure and links.
- Python script edits: run focused tests when present, or at least `python3 -m compileall` on changed script directories.
- `fin-ai-daily-brief` edits: run `python3 -m pytest tests/test_fin_ai_daily_brief.py`.
- Cross-skill changes: run the relevant skill scripts with dry-run or fixture input when available.

After edits, show `git status --short --branch`, stage only the intended files, and commit the relevant changes when the user asked for repository modifications.
