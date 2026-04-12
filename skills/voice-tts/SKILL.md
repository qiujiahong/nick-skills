---
name: voice-tts
description: 本地语音合成 / TTS。Use when the user asks to synthesize speech, generate narration audio, create local TTS output, use microsoft/VibeVoice-1.5B, or generate teaching-video narration. Uses local VibeVoice only; do not call remote/cloud TTS APIs.
---

# Voice TTS

把文本合成为本地音频。默认使用本机部署的 `microsoft/VibeVoice-1.5B`，不调用火山、OpenSpeech 或其他远程 TTS API。

## Core Rules

- 本 skill 只做本地 TTS。不要上传文本或声音参考到远程 TTS 服务。
- 首选 `scripts/tts.py`。它会自动调用 `scripts/ensure_vibevoice.sh`，缺本地部署时先部署。
- 默认输出 wav；需要 mp3 时用 `--format mp3` 或输出 `.mp3`，脚本会用 ffmpeg 转码。
- 同一条视频或同一批旁白必须固定 speaker、seed、cfg scale 和 voice reference。
- 声音克隆只在用户提供授权本地 `.wav` 参考音频时使用。

详细 VibeVoice 接入见 [VibeVoice integration](references/vibevoice-integration.md)。

## Environment

常用变量：

- `VIBEVOICE_MODEL`：默认 `microsoft/VibeVoice-1.5B`
- `VIBEVOICE_SPEAKER_ID`：中文默认 `Bowen`，英文默认 `Alice`
- `VIBEVOICE_SEED`：默认 `1227`
- `VIBEVOICE_CFG_SCALE`：默认 `1.3`
- `VIBEVOICE_LANGUAGE`：默认 `zh`
- `VIBEVOICE_VOICE_REF`：授权声音参考 `.wav`
- `VIBEVOICE_DEPLOY_DIR`：默认 `$HOME/.cache/nick-skills/vibevoice`

部署后会写入：

```bash
$HOME/.cache/nick-skills/vibevoice/env.sh
```

## Usage

```bash
# 自动确保本地 VibeVoice 可用，并生成 wav
python3 skills/voice-tts/scripts/tts.py "要合成的文本" -o output.wav

# 从文件读取
python3 skills/voice-tts/scripts/tts.py -f narration.txt -o output.wav

# 指定 speaker / seed，保证多段旁白稳定
python3 skills/voice-tts/scripts/tts.py -f scene.txt -o scene-01.wav \
  --speaker-id Bowen --seed 1227

# 使用授权参考音频
python3 skills/voice-tts/scripts/tts.py "测试" -o cloned.wav \
  --voice-ref /absolute/path/to/authorized-reference.wav

# 输出 mp3
python3 skills/voice-tts/scripts/tts.py "测试" -o output.mp3 --format mp3
```

## Scripts

- `scripts/ensure_vibevoice.sh`：部署/复用本地 VibeVoice，缓存 `microsoft/VibeVoice-1.5B`。
- `scripts/tts.py`：通用本地 TTS 入口。
- `scripts/vibevoice_tts_adapter.py`：命令适配器，直接调用 VibeVoice community inference。
- `scripts/check_audio_consistency.py`：检测多段音频是否出现音色或音调异常。

## Voice Director Markers

`voice-director` 可能输出 `[emotion=... speed=... pitch=...]文本[/]` 标记。本地 VibeVoice 当前不使用这些远程 TTS 控制参数，`scripts/tts.py` 默认会去掉标记并保留文本内容。确实要保留原文标记时使用 `--keep-markers`。

## Quality Gate

生成一组旁白后：

```bash
$VIBEVOICE_VENV/bin/python skills/voice-tts/scripts/check_audio_consistency.py audio
```

如果某段被标为 outlier，用同一 speaker / seed / cfg scale / voice reference 重新生成该段；不要用随机参数单独补一段。
