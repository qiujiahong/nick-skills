# nick-skills

OpenClaw Agent Skills 集合。

## 技能列表

| Skill | 描述 |
|-------|------|
| [image-gen](skills/image-gen/) | AI 图像生成与编辑，支持文生图、图+文生图、风格转换，多比例与标准/2K/4K 分辨率 |
| [video-gen](skills/video-gen/) | AI 视频生成与编辑，使用火山引擎 Doubao Seedance，支持文生视频、图生视频、有声视频 |
| [openclaw-codex-account-switch](skills/openclaw-codex-account-switch/) | 指导在 Linux + OpenClaw + Clash Meta 环境中切换/重配 OpenAI Codex 账号，并完成端到端验证 |
| [voice-tts](skills/voice-tts/) | 火山引擎语音合成，支持声音复刻音色、情感/语速/语调控制 |
| [voice-director](skills/voice-director/) | 语音导演，AI 自动为台词标注情感和语速语调 |

## 使用方法

将 `skills/` 下的技能目录复制到 OpenClaw 的 skills 目录中即可使用。

## 环境变量

### image-gen

```bash
export IMAGE_GEN_API_KEY="your-api-key"
export IMAGE_GEN_BASE_URL="https://code.newcli.com/gemini"  # 可选
```

### video-gen

```bash
export VIDEO_GEN_API_KEY="your-api-key"
export VIDEO_GEN_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"  # 可选
```

### voice-tts

```bash
export NICK_SKILLS_ENV_VOICE_TTS_API_KEY="your-api-key"
export NICK_SKILLS_ENV_VOICE_TTS_VOICE_TYPE="S_xxxxxxxx"  # 可选，默认音色
```
