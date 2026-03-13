# nick-skills

OpenClaw Agent Skills 集合。

## 技能列表

| Skill | 描述 |
|-------|------|
| [voice-tts](skills/voice-tts/) | 火山引擎语音合成，支持声音复刻音色 |

## 使用方法

将 `skills/` 下的技能目录复制到 OpenClaw 的 skills 目录中即可使用。

## 环境变量

### voice-tts

```bash
export VOICE_TTS_API_KEY="your-api-key"
export VOICE_TTS_VOICE_TYPE="S_xxxxxxxx"  # 可选，默认音色
```
