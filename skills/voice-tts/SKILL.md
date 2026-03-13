---
name: voice-tts
description: 火山引擎语音合成（支持声音复刻音色）。当用户要求语音合成、文字转语音、TTS、用克隆声音朗读时使用此 skill。支持语速、语调、情感控制和 SSML。
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
  --pitch 1.0 \
  --emotion happy \
  --encoding mp3
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `text`（必填） | 要合成的文本（或 SSML） | — |
| `--voice, -v` | 音色 ID | 环境变量或 `BV001_V2` |
| `--output, -o` | 输出文件路径 | `tts_output.mp3` |
| `--speed, -s` | 语速（0.5~2.0） | `1.0` |
| `--pitch, -p` | 语调（0.5~2.0），>1 偏高 <1 偏低 | `1.0` |
| `--emotion` | 情感标签 | 无 |
| `--ssml` | 输入为 SSML 格式 | 关 |
| `--encoding, -e` | 音频格式（mp3/wav/ogg_opus） | `mp3` |
| `--cluster, -c` | 集群名称 | 环境变量或 `volcano_icl` |

## 语气与情感控制

### 方式一：emotion 参数（简单）

直接指定情感标签：

| 标签 | 情感 |
|------|------|
| `happy` | 开心、愉快 |
| `sad` | 悲伤、低落 |
| `angry` | 生气、愤怒 |
| `scare` | 恐惧、害怕 |
| `hate` | 厌恶 |
| `surprise` | 惊讶 |
| `neutral` | 中性、平静 |

```bash
python3 scripts/tts.py "太棒了，我好开心！" --emotion happy
python3 scripts/tts.py "这件事让我很难过。" --emotion sad --pitch 0.9 --speed 0.8
```

### 方式二：pitch + speed 组合（灵活）

通过调节语调和语速模拟不同语气：

| 效果 | speed | pitch |
|------|-------|-------|
| 兴奋 | 1.2 | 1.2 |
| 低沉沉稳 | 0.8 | 0.8 |
| 温柔轻声 | 0.9 | 1.1 |
| 急促紧张 | 1.4 | 1.1 |
| 庄重播报 | 0.85 | 0.95 |

### 方式三：SSML（精细控制）

SSML 可以在同一段文本中混合不同的语气、停顿、语速：

```bash
python3 scripts/tts.py '<speak>
<emotion category="happy" intensity="1.0">今天天气真不错！</emotion>
<break time="500ms"/>
<prosody rate="slow" pitch="low">不过明天可能会下雨。</prosody>
<break time="300ms"/>
<prosody rate="fast" pitch="high">赶紧出去玩吧！</prosody>
</speak>' --ssml
```

#### SSML 常用标签

| 标签 | 作用 | 示例 |
|------|------|------|
| `<speak>` | 根标签 | `<speak>...</speak>` |
| `<emotion>` | 情感控制 | `<emotion category="happy" intensity="1.0">开心</emotion>` |
| `<prosody>` | 语速/音调 | `<prosody rate="fast" pitch="high">快说</prosody>` |
| `<break>` | 停顿 | `<break time="500ms"/>` |
| `<say-as>` | 特殊读法 | `<say-as interpret-as="digits">123</say-as>` |

## 常用音色

### 复刻音色

在火山引擎控制台创建的声音复刻音色，格式如 `S_xxxxxxxx`。

### 预置音色示例

| 音色 ID | 描述 |
|---------|------|
| `BV001_V2` | 通用女声 |
| `BV002_V2` | 通用男声 |

更多预置音色参见 [火山引擎文档](https://www.volcengine.com/docs/6561/97465)。

## 集群说明

| 集群 | 说明 |
|------|------|
| `volcano_icl` | 即时声音克隆，支持复刻音色 |
| `volcano_tts` | 标准语音合成，仅支持预置音色 |
| `volcano_mega` | 高级语音合成 |

## 工作流程

1. **接收文本** — 用户提供要朗读的文字
2. **确定语气** — 根据语境选择 emotion / pitch / speed 或 SSML
3. **调用脚本** — 执行 `scripts/tts.py` 生成音频
4. **发送音频** — 上传到飞书并发送文件消息

## 示例

```bash
# 基础合成
python3 scripts/tts.py "从前有座山，山上有座庙"

# 开心语气
python3 scripts/tts.py "太好了！我们成功了！" --emotion happy --speed 1.1

# 低沉叙述
python3 scripts/tts.py "那是一个寒冷的冬夜..." --pitch 0.85 --speed 0.85

# SSML 混合语气
python3 scripts/tts.py '<speak><prosody rate="slow">很久很久以前</prosody><break time="500ms"/><emotion category="surprise">突然出现了一条龙！</emotion></speak>' --ssml

# 输出 wav 格式
python3 scripts/tts.py "测试音频" --encoding wav --output test.wav
```
