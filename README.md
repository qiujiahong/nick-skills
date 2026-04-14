# nick-skills

Reusable OpenClaw / Codex skills for research, media generation, technical blog production, publishing, and financial AI brief automation.

## Skills

| Skill | Purpose |
| --- | --- |
| [ai-topic-research](skills/ai-topic-research/) | Research AI technology topics or discover one timely blog topic from current technical community discussions. |
| [countryhuman-video-maker](skills/countryhuman-video-maker/) | Produce CH / countryhuman style voiced dialogue videos with script, storyboard, local narration, rendered MP4, and publish-ready copy. |
| [fin-ai-daily-brief](skills/fin-ai-daily-brief/) | Search financial AI news with the local Tavily wrapper, select the most valuable items for financial enterprises, render an HTML brief, and email subscribers through SMTP. |
| [image-gen](skills/image-gen/) | Generate and edit images from text, one reference image, or multiple reference images. |
| [tavily-search](skills/tavily-search/) | Tavily Search API wrapper with multiple-key rotation, fallback, structured JSON output, and domain / recency controls. |
| [teaching-video-maker](skills/teaching-video-maker/) | Create voiced explainer, tutorial, lecture, and product teaching videos by orchestrating Remotion visuals and local `voice-tts` narration. |
| [tech-blog-writer](skills/tech-blog-writer/) | Turn a selected topic, research notes, and writing guidance into a blog folder with `blog.md`, `image-requirements.md`, and `assets/`. |
| [video-gen](skills/video-gen/) | Generate AI video with Doubao Seedance, including text-to-video, image-to-video, and audio video modes. |
| [voice-tts](skills/voice-tts/) | Local TTS based on `microsoft/VibeVoice-1.5B`; no remote TTS API calls by default. |
| [wechat-mp-publisher](skills/wechat-mp-publisher/) | Render Markdown / HTML for WeChat Official Account, upload images, create drafts, and publish only when explicitly requested. |

`agent-provisioning` has been removed from this repository.

## Layout

```text
.
├── AGENTS.md
├── README.md
├── skills/
│   ├── ai-topic-research/
│   ├── countryhuman-video-maker/
│   ├── fin-ai-daily-brief/
│   ├── image-gen/
│   ├── tavily-search/
│   ├── teaching-video-maker/
│   ├── tech-blog-writer/
│   ├── video-gen/
│   ├── voice-tts/
│   └── wechat-mp-publisher/
└── tests/
```

Most skills use this shape:

```text
skills/<skill-name>/
  SKILL.md
  README.md
  scripts/
  references/
  .env.example
```

Not every skill needs every optional file.

## Installation

Copy or link the skill directory you need into your OpenClaw / Codex skills directory:

```bash
cp -R skills/<skill-name> /path/to/openclaw/skills/
```

When a skill depends on another local skill, copy the dependency too. For example, `ai-topic-research` and `fin-ai-daily-brief` depend on `tavily-search`; `teaching-video-maker` and `countryhuman-video-maker` depend on `voice-tts` for local narration.

## Common Workflows

### Technical Blog Pipeline

Use this sequence for a complete technical blog:

1. `ai-topic-research`: discover or research the topic.
2. Add one more focused research pass for usable facts, cases, and source notes.
3. `tech-blog-writer`: create the blog folder with Markdown and image requirements.
4. `image-gen`: generate the cover and body images into `assets/`.
5. `wechat-mp-publisher`: render locally, create a WeChat draft, and publish only after confirmation.

Expected blog output:

```text
tech-blog-writer/YYYYMMDD/<topic-slug>/
  blog.md
  image-requirements.md
  assets/
```

### Teaching Video Pipeline

Use `teaching-video-maker` for explainer or tutorial videos. It delegates visuals to a Remotion skill and narration to `voice-tts`.

```bash
skills/voice-tts/scripts/ensure_vibevoice.sh
source "$HOME/.cache/nick-skills/vibevoice/env.sh"
```

Typical output:

```text
teaching-video/YYYYMMDD/<topic-slug>/
  brief.md
  outline.md
  narration.md
  storyboard.md
  timing.json
  audio/
  remotion/
  output/
```

### Countryhuman Video Pipeline

Use `countryhuman-video-maker` for CH / countryhuman style multi-character dialogue videos. It creates scripts, storyboard, local voiceover, rendered MP4, and short publishing copy.

Typical output:

```text
countryhuman-video/YYYYMMDD/<topic-slug>/
  brief.md
  dialogue.json
  script.md
  storyboard.md
  timing.json
  sources.md
  audio/
  frames/
  segments/
  output/
```

### Financial AI Daily Brief

Use `fin-ai-daily-brief` to search recent financial AI news, keep the top 15 search results, select 10 valuable items for financial enterprises, render a single-page HTML brief, and email subscribers.

```bash
python3 skills/fin-ai-daily-brief/scripts/generate_fin_ai_brief.py \
  --query "金融 AI" \
  --topic news \
  --output-dir ./output \
  --send-email
```

Use `FIN_AI_SUBSCRIBERS` or `FIN_AI_SUBSCRIBERS_FILE` to manage recipients.

## Environment

Use local `.env` or `.env.local` files for real credentials. Commit only examples.

| Skill | Key variables |
| --- | --- |
| `ai-topic-research` | `TAVILY_API_KEYS`, `TAVILY_API_KEY`, `TAVILY_SEARCH_BASE_URL` |
| `fin-ai-daily-brief` | `TAVILY_API_KEYS`, `FIN_AI_SMTP_HOST`, `FIN_AI_SMTP_PORT`, `FIN_AI_SMTP_USER`, `FIN_AI_SMTP_PASS`, `FIN_AI_SUBSCRIBERS`, `FIN_AI_SUBSCRIBERS_FILE` |
| `image-gen` | `IMAGE_GEN_API_KEY`, `IMAGE_GEN_BASE_URL`, `IMAGE_GEN_MODEL`, `IMAGE_GEN_ASPECT_RATIO`, `IMAGE_GEN_IMAGE_SIZE` |
| `tavily-search` | `TAVILY_API_KEYS`, `TAVILY_API_KEY`, `TAVILY_SEARCH_BASE_URL` |
| `video-gen` | `VIDEO_GEN_API_KEY`, `VIDEO_GEN_BASE_URL` |
| `voice-tts` | `VIBEVOICE_MODEL`, `VIBEVOICE_SPEAKER_ID`, `VIBEVOICE_SEED`, `VIBEVOICE_CFG_SCALE`, `VIBEVOICE_LANGUAGE`, `VIBEVOICE_VOICE_REF` |
| `wechat-mp-publisher` | `WECHAT_MP_APP_ID`, `WECHAT_MP_APP_SECRET`, `WECHAT_MP_THUMB_MEDIA_ID`, `WECHAT_MP_AUTHOR` |

## Development

Before editing, inspect the target skill's `SKILL.md` and existing scripts. Keep changes local to the skill unless a shared workflow or root documentation needs to change.

Useful checks:

```bash
git status --short --branch
python3 -m pytest tests/test_fin_ai_daily_brief.py
python3 -m compileall skills tests
```

Do not stage unrelated local changes. This repository may contain local `.env` files or generated work products that should stay private.
