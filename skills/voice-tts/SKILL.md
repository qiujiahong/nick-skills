---
name: voice-tts
description: 火山引擎语音合成（支持声音复刻音色）。当用户要求语音合成、文字转语音、TTS、用克隆声音朗读时使用此 skill。
---

# 语音合成 (Voice TTS)

基于火山引擎 OpenSpeech API，支持使用声音复刻音色进行语音合成。

## 环境变量

所有环境变量统一使用 `NICK_SKILLS_ENV_` 前缀，避免冲突。

- `NICK_SKILLS_ENV_VOICE_TTS_API_KEY` — 火山引擎语音技术 API Key（必填）
- `NICK_SKILLS_ENV_VOICE_TTS_VOICE_TYPE` — 默认音色 ID（可选，默认 `BV001_V2`）
- `NICK_SKILLS_ENV_VOICE_TTS_CLUSTER` — 集群名称（可选，默认 `volcano_icl`）

## 使用方法

```bash
python3 scripts/tts.py "要合成的文本" \
  --voice YOUR_VOICE_ID \
  --output output.mp3 \
  --speed 1.0 \
  --encoding mp3
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `text`（必填） | 要合成的文本 | — |
| `--voice, -v` | 音色 ID（复刻音色或预置音色） | 环境变量或 `BV001_V2` |
| `--output, -o` | 输出文件路径 | `tts_output.mp3` |
| `--speed, -s` | 语速（0.5~2.0） | `1.0` |
| `--encoding, -e` | 音频格式（mp3/wav/ogg_opus） | `mp3` |
| `--cluster, -c` | 集群名称 | 环境变量或 `volcano_icl` |

## 常用音色

### 复刻音色

使用火山引擎控制台创建的声音复刻音色 ID，格式如 `S_xxxxxxxx`。

### 预置音色示例

| 音色 ID | 描述 |
|---------|------|
| `BV001_V2` | 通用女声 |
| `BV002_V2` | 通用男声 |

更多预置音色参见 [火山引擎文档](https://www.volcengine.com/docs/6561/97465)。

## 集群说明

| 集群 | 说明 |
|------|------|
| `volcano_icl` | 即时声音克隆（Instant Clone），支持复刻音色 |
| `volcano_tts` | 标准语音合成，仅支持预置音色 |
| `volcano_mega` | 高级语音合成 |

## 工作流程

1. **接收文本** — 用户提供要朗读的文字
2. **选择音色** — 使用用户指定的或默认音色
3. **调用脚本** — 执行 `scripts/tts.py` 生成音频
4. **发送音频** — 上传到飞书并发送文件消息

## 示例

```bash
# 使用复刻音色
python3 scripts/tts.py "从前有座山，山上有座庙" --voice YOUR_VOICE_ID

# 使用预置音色，加快语速
python3 scripts/tts.py "今天天气真不错" --voice BV001_V2 --speed 1.2

# 输出 wav 格式
python3 scripts/tts.py "测试音频" --voice YOUR_VOICE_ID --encoding wav --output test.wav
```
