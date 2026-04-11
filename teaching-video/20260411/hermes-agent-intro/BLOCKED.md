# 当前阻塞：本地 VibeVoice TTS 不可用

本视频按 `teaching-video-maker` 规则要求使用本地 VibeVoice 生成旁白。

已检查：

- 未发现 `VIBEVOICE_ENDPOINT`、`VIBEVOICE_TTS_CMD`、`VIBEVOICE_VOICE_REF` 等环境变量。
- `http://127.0.0.1:7860/` 返回 `502 Bad Gateway`，不像可用的 VibeVoice TTS 服务。
- 当前 Python 环境没有 `vibevoice`、`torch`、`transformers` 包。
- 未发现 `vibevoice` 或 `vibevoice_tts` CLI。
- Remotion skill 已安装到 `~/.agents/skills/remotion`。
- Remotion 项目已创建，TypeScript 检查通过。
- Remotion composition 已验证可识别：`HermesAgentIntro`，1920x1080，30fps，草稿 182 秒。
- 直接运行 `/usr/local/bin/node` 是 Node 14，会让 Remotion CLI 报 `Cannot find module 'node:fs'`；使用登录 shell / nvm 的 Node 22 可正常识别 composition。

额外查证：

- Microsoft VibeVoice 官方仓库说明里，`VibeVoice-TTS-1.5B` quick try 当前标为 `Disabled`。
- 官方仓库说明里提到 VibeVoice-TTS 代码已从仓库移除。

下一步：

1. 启动本地 VibeVoice TTS 服务，并设置 `VIBEVOICE_ENDPOINT`。
2. 或提供 `VIBEVOICE_TTS_CMD` 命令模板。
3. 如需声音克隆，设置 `VIBEVOICE_VOICE_REF=/absolute/path/to/authorized-reference.wav`。
4. 重新生成 `audio/scene-01.wav` 到 `audio/scene-07.wav`。
5. 用 `ffprobe` 测真实时长，生成正式 `timing.json`。
6. 用 Remotion 渲染最终有声 mp4。

可用命令：

```bash
cd teaching-video/20260411/hermes-agent-intro
export VIBEVOICE_ENDPOINT="http://127.0.0.1:7860"
python3 scripts/generate_audio_with_vibevoice.py
cd remotion
zsh -lic 'npm run render'
```
