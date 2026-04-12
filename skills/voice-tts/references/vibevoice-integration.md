# VibeVoice Integration

`voice-tts` uses local VibeVoice only. Do not call remote/cloud TTS APIs.

## Local Deployment

Before generating audio, ensure `microsoft/VibeVoice-1.5B` is available locally:

```bash
skills/voice-tts/scripts/ensure_vibevoice.sh
source "$HOME/.cache/nick-skills/vibevoice/env.sh"
```

The script creates a local venv, downloads or reuses a VibeVoice TTS implementation, caches `microsoft/VibeVoice-1.5B` through Hugging Face, and writes:

```bash
$HOME/.cache/nick-skills/vibevoice/env.sh
```

The managed deployment defaults to the community-preserved VibeVoice TTS implementation as a loader for Microsoft model weights, because the restored Microsoft VibeVoice repository does not include the original TTS code.

## Environment Variables

- `VOICE_TTS_ENGINE`：默认 `vibevoice`
- `VIBEVOICE_MODEL`：默认 `microsoft/VibeVoice-1.5B`
- `VIBEVOICE_TTS_CMD`：本地命令模板
- `VOICE_TTS_ALLOW_CUSTOM_CMD`：设为 `1` 时，`ensure_vibevoice.sh` 复用已有 `VIBEVOICE_TTS_CMD`
- `VIBEVOICE_VOICE_REF`：授权声音克隆参考音频路径，必须是本地 `.wav`
- `VIBEVOICE_SPEAKER_ID`：本地 voice preset；托管中文默认 `Bowen`
- `VIBEVOICE_SEED`：默认 `1227`；同一条视频必须固定
- `VIBEVOICE_CFG_SCALE`：默认 `1.3`；同一条视频必须固定
- `VIBEVOICE_LANGUAGE`：默认 `zh`

## Command Template Contract

`VIBEVOICE_TTS_CMD` may contain these placeholders:

- `{model}`
- `{text}`
- `{text_file}`
- `{output}`
- `{voice_ref}`
- `{speaker_id}`
- `{language}`
- `{seed}`

Prefer `{text_file}` for long narration to avoid shell quoting problems.

Managed deployment example:

```bash
export VIBEVOICE_TTS_CMD="$HOME/.cache/nick-skills/vibevoice/.venv/bin/python skills/voice-tts/scripts/vibevoice_tts_adapter.py --source-dir $HOME/.cache/nick-skills/vibevoice/source --model {model} --text-file {text_file} --output {output} --voice-ref {voice_ref} --speaker-id {speaker_id} --language {language} --seed {seed}"
```

## Scene Audio Rules

- Generate one audio file per scene, not one giant narration file.
- Keep filenames stable: `audio/scene-01.wav`, `audio/scene-02.wav`, etc.
- Keep speaker, seed, cfg scale, language, and reference audio identical across all scenes in one video.
- After generation, measure real duration with `ffprobe`.
- Save actual durations into the caller's timing contract.
- If pronunciation is wrong for technical terms, add a pronunciation note to the scene text and regenerate only that scene.
- If one scene has a different tone or pitch, regenerate it with the same locked settings.
- Run a rough outlier check before rendering:

```bash
$VIBEVOICE_VENV/bin/python skills/voice-tts/scripts/check_audio_consistency.py teaching-video/YYYYMMDD/<topic-slug>/audio
```

## Voice Clone Rules

- Use voice cloning only when the user provides a local reference audio file and has rights to use that voice.
- Keep reference audio local; do not upload it to external services.
- Record in the final response whether cloned voice was used.
- Prefer natural, steady narration over exaggerated emotion.
