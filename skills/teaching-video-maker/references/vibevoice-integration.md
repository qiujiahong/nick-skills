# VibeVoice Integration

Use local VibeVoice for all narration unless the user explicitly allows another TTS engine.

Do not hard-code one official CLI shape. VibeVoice local deployments can differ, so use the endpoint/command adapter below and inspect the local deployment when needed.

## Local Deployment First

Before generating audio, verify that `microsoft/VibeVoice-1.5B` is available locally. Run:

```bash
scripts/ensure_vibevoice.sh
```

The script checks, in order:

1. `VIBEVOICE_ENDPOINT` for an already-running local HTTP service.
2. `VIBEVOICE_TTS_CMD` for an existing local command adapter.
3. A managed local command deployment under `$HOME/.cache/nick-skills/vibevoice`.

If deployment is needed, the script installs a local Python venv, downloads or reuses a VibeVoice TTS implementation, caches `microsoft/VibeVoice-1.5B` through Hugging Face, and writes:

```bash
$HOME/.cache/nick-skills/vibevoice/env.sh
```

Load that file before scene generation:

```bash
source "$HOME/.cache/nick-skills/vibevoice/env.sh"
```

Microsoft restored the official VibeVoice repository without the original TTS code. The default managed deployment therefore uses the community-preserved TTS implementation as a loader for Microsoft model weights. Prefer a user-provided internal endpoint or command when one is available.

## Environment Variables

- `TEACHING_VIDEO_TTS_ENGINE`：默认 `vibevoice`
- `VIBEVOICE_MODEL`：默认 `microsoft/VibeVoice-1.5B`
- `VIBEVOICE_ENDPOINT`：本地 HTTP 服务地址，例如 `http://127.0.0.1:7860`
- `VIBEVOICE_TTS_CMD`：本地命令模板，HTTP 不可用时使用
- `VIBEVOICE_VOICE_REF`：授权声音克隆参考音频路径
- `VIBEVOICE_SPEAKER_ID`：本地服务已有 speaker / voice id；托管中文默认 `Bowen`
- `VIBEVOICE_SEED`：默认 `1227`；同一条视频必须固定，避免各 scene 音色或音高漂移
- `VIBEVOICE_CFG_SCALE`：默认 `1.3`；同一条视频必须固定
- `VIBEVOICE_LANGUAGE`：默认 `zh`
- `VIBEVOICE_AUDIO_FORMAT`：默认 `wav`

## Invocation Order

1. Prefer `VIBEVOICE_ENDPOINT` when set.
2. Else use `VIBEVOICE_TTS_CMD` when set.
3. Else run `scripts/ensure_vibevoice.sh`, then `source` the generated env file and use its `VIBEVOICE_TTS_CMD`.
4. If local deployment fails, stop and report the setup error. Do not silently switch to cloud TTS.

## HTTP Contract

Different local deployments may expose different routes. Prefer a simple adapter endpoint that accepts one scene at a time:

```json
{
  "model": "microsoft/VibeVoice-1.5B",
  "text": "本段旁白文本",
  "language": "zh",
  "speaker_id": "optional-speaker-id",
  "voice_reference": "/abs/path/to/reference.wav",
  "output_path": "/abs/path/to/audio/scene-01.wav",
  "format": "wav"
}
```

If the service returns audio bytes, save them to `output_path`. If it returns a file path or URL, copy or download it into the scene audio path.

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

Example:

```bash
export VIBEVOICE_TTS_CMD='python /path/to/vibevoice_tts.py --model {model} --text-file {text_file} --output {output} --voice-ref {voice_ref} --speaker-id {speaker_id} --language {language} --seed {seed}'
```

Managed deployment example:

```bash
source "$HOME/.cache/nick-skills/vibevoice/env.sh"
python teaching-video/YYYYMMDD/<topic-slug>/scripts/generate_audio_with_vibevoice.py
```

## Scene Audio Rules

- Generate one audio file per scene, not one giant narration file.
- Keep filenames stable: `audio/scene-01.wav`, `audio/scene-02.wav`, etc.
- Keep speaker, seed, cfg scale, language, and reference audio identical across all scenes in one video.
- After generation, measure real duration with `ffprobe`.
- Save actual durations into `timing.json`.
- If pronunciation is wrong for technical terms, add a pronunciation note to the scene text and regenerate only that scene.
- If one scene has a different tone or pitch, regenerate it with the same locked settings. For the managed deployment, you can target only that scene with `TEACHING_VIDEO_SCENE_IDS=scene-06 python scripts/generate_audio_with_vibevoice.py`.
- Run a rough outlier check before rendering:

```bash
$VIBEVOICE_VENV/bin/python skills/teaching-video-maker/scripts/check_audio_consistency.py teaching-video/YYYYMMDD/<topic-slug>/audio
```

## Voice Clone Rules

- Use voice cloning only when the user provides a local reference audio file and has rights to use that voice.
- Keep reference audio local; do not upload it to external services.
- Record in the final response whether cloned voice was used.
- For teaching videos, prefer natural, steady narration over exaggerated emotion.

## Reference

- VibeVoice repository: https://github.com/microsoft/VibeVoice
