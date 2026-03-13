# nick-skills

OpenClaw Agent Skills 集合。

## 技能列表

| Skill | 描述 |
|-------|------|
| [voice-tts](skills/voice-tts/) | 火山引擎语音合成，支持声音复刻音色、情感/语速/语调控制 |
| [voice-director](skills/voice-director/) | 语音导演，AI 自动为台词标注情感和语速语调 |

## 使用方法

将 `skills/` 下的技能目录复制到 OpenClaw 的 skills 目录中即可使用。

## 环境变量

### voice-tts

```bash
export NICK_SKILLS_ENV_VOICE_TTS_API_KEY="your-api-key"
export NICK_SKILLS_ENV_VOICE_TTS_VOICE_TYPE="S_xxxxxxxx"  # 可选，默认音色
```
