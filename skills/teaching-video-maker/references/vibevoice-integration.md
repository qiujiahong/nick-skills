# VibeVoice Integration

Use local VibeVoice for all narration unless the user explicitly allows another TTS engine.

Do not hard-code one official CLI shape. VibeVoice local deployments can differ, so use the endpoint/command adapter below and inspect the local deployment when needed.

## Environment Variables

- `TEACHING_VIDEO_TTS_ENGINE`：默认 `vibevoice`
- `VIBEVOICE_MODEL`：默认 `microsoft/VibeVoice-1.5B`
- `VIBEVOICE_ENDPOINT`：本地 HTTP 服务地址，例如 `http://127.0.0.1:7860`
- `VIBEVOICE_TTS_CMD`：本地命令模板，HTTP 不可用时使用
- `VIBEVOICE_VOICE_REF`：授权声音克隆参考音频路径
- `VIBEVOICE_SPEAKER_ID`：本地服务已有 speaker / voice id
- `VIBEVOICE_LANGUAGE`：默认 `zh`
- `VIBEVOICE_AUDIO_FORMAT`：默认 `wav`

## Invocation Order

1. Prefer `VIBEVOICE_ENDPOINT` when set.
2. Else use `VIBEVOICE_TTS_CMD` when set.
3. Else inspect the local VibeVoice deployment and adapt to its documented CLI/API.
4. If no local VibeVoice deployment is available, stop and report the missing setup. Do not silently switch to cloud TTS.

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

Prefer `{text_file}` for long narration to avoid shell quoting problems.

Example:

```bash
export VIBEVOICE_TTS_CMD='python /path/to/vibevoice_tts.py --model {model} --text-file {text_file} --output {output} --voice-ref {voice_ref} --language {language}'
```

## Scene Audio Rules

- Generate one audio file per scene, not one giant narration file.
- Keep filenames stable: `audio/scene-01.wav`, `audio/scene-02.wav`, etc.
- After generation, measure real duration with `ffprobe`.
- Save actual durations into `timing.json`.
- If pronunciation is wrong for technical terms, add a pronunciation note to the scene text and regenerate only that scene.

## Voice Clone Rules

- Use voice cloning only when the user provides a local reference audio file and has rights to use that voice.
- Keep reference audio local; do not upload it to external services.
- Record in the final response whether cloned voice was used.
- For teaching videos, prefer natural, steady narration over exaggerated emotion.

## Reference

- VibeVoice repository: https://github.com/microsoft/VibeVoice
