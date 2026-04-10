# nick-skills

OpenClaw / Codex 可复用技能集合，包含图像生成、视频生成、语音合成、语音导演，以及 OpenClaw 团队配置类 skill。

## 目录结构

```text
skills/
  image-gen/
  video-gen/
  voice-tts/
  voice-director/
  ai-topic-research/
  tech-blog-writer/
  openclaw-team-setup/
  openclaw-codex-account-switch/
  agent-provisioning/
  fin-ai-daily-brief/
dist/
```

`skills/` 下是可直接使用的 skill 源码目录，`dist/` 下是已打包产物。

## Skill 列表

| Skill | 描述 |
|-------|------|
| [image-gen](skills/image-gen/) | AI 图像生成与编辑，支持文生图、图+文生图、风格转换，多比例与标准 / 2K / 4K 分辨率 |
| [video-gen](skills/video-gen/) | AI 视频生成与编辑，基于火山引擎 Doubao Seedance，支持文生视频、图生视频、有声视频 |
| [voice-tts](skills/voice-tts/) | 火山引擎语音合成，支持声音复刻音色、语速 / 语调 / 情感控制 |
| [voice-director](skills/voice-director/) | 用 LLM 为台词自动标注情感、语速、语调，再交给 `voice-tts` 合成 |
| [ai-topic-research](skills/ai-topic-research/) | 面向 AI 技术主题与技术社区热点的联网研究；既能研究单个主题，也能从社区热点里只推荐 1 个适合写博客的主题 |
| [tech-blog-writer](skills/tech-blog-writer/) | 根据“已选主题 + 支撑链接 + 写作建议”生成技术博客初稿，并在合适位置自动预留配图占位符 |
| [openclaw-team-setup](skills/openclaw-team-setup/) | 标准化配置或修复 OpenClaw 多智能体团队，覆盖 agent 拓扑、ACP、Feishu 路由与验证 |
| [openclaw-codex-account-switch](skills/openclaw-codex-account-switch/) | 在 OpenClaw 环境中切换或重配 OpenAI Codex 账号，并完成登录与连通性验收 |
| [agent-provisioning](skills/agent-provisioning/) | 创建或修复单个 OpenClaw / ACP agent，并绑定指定的 Feishu 机器人与 routing binding |
| [fin-ai-daily-brief](skills/fin-ai-daily-brief/) | 搜索 20 条金融 + AI 资讯，筛选出最有价值的 10 条，生成 HTML 资讯页并通过 SMTP 邮件发送 |

## 安装方式

按需将目标 skill 目录复制或链接到你的 OpenClaw skills 目录中即可。

```bash
cp -R skills/<skill-name> /path/to/openclaw/skills/
```

如果你的环境支持打包分发，也可以直接使用 `dist/` 下的产物。

## 环境变量

不同 skill 使用不同环境变量：

### image-gen

```bash
export IMAGE_GEN_API_KEY="your-api-key"
export IMAGE_GEN_BASE_URL="https://api.apiyi.com"
export IMAGE_GEN_MODEL="gemini-3.1-flash-image-preview"
export IMAGE_GEN_ASPECT_RATIO="16:9"
export IMAGE_GEN_IMAGE_SIZE="2K"
```

### video-gen

```bash
export VIDEO_GEN_API_KEY="your-api-key"
export VIDEO_GEN_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
```

### voice-tts

```bash
export NICK_SKILLS_ENV_VOICE_TTS_API_KEY="your-api-key"
export NICK_SKILLS_ENV_VOICE_TTS_VOICE_TYPE="S_xxxxxxxx"
export NICK_SKILLS_ENV_VOICE_TTS_CLUSTER="volcano_icl"
```

### voice-director

```bash
export NICK_SKILLS_ENV_DIRECTOR_API_KEY="your-api-key"
export NICK_SKILLS_ENV_DIRECTOR_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
export NICK_SKILLS_ENV_DIRECTOR_MODEL="doubao-1.5-pro-256k"
```

### ai-topic-research

```bash
export TAVILY_API_KEYS="tvly-key-1,tvly-key-2"
export TAVILY_SEARCH_BASE_URL="https://api.tavily.com"
```

## 使用建议

- 图像生成直接看 [image-gen](skills/image-gen/)。
- 视频生成直接看 [video-gen](skills/video-gen/)。
- 需要更有表现力的配音时，先用 [voice-director](skills/voice-director/) 标注，再用 [voice-tts](skills/voice-tts/) 合成。
- 需要围绕 `MCP`、`RAG`、`AI Coding Agent`、`Responses API` 这类主题快速做第一轮资料研究时，使用 [ai-topic-research](skills/ai-topic-research/)。
- 需要把“选题 + 支撑链接 + 写作建议”扩写成技术博客初稿时，使用 [tech-blog-writer](skills/tech-blog-writer/)。
- 需要搭建或修复 OpenClaw 项目团队时，使用 [openclaw-team-setup](skills/openclaw-team-setup/)。
- 需要切换 OpenClaw 上的 Codex OAuth 账号时，使用 [openclaw-codex-account-switch](skills/openclaw-codex-account-switch/)。
- 需要新建单个 agent、绑定 Feishu 机器人并校验状态时，使用 [agent-provisioning](skills/agent-provisioning/)。
- 需要生成金融 AI 日报、邮件订阅资讯页时，使用 [fin-ai-daily-brief](skills/fin-ai-daily-brief/)。
