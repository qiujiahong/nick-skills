---
name: teaching-video-maker
description: 生成有声音的教学视频。Use when the user asks to create an explainer, course clip, tutorial, lecture-style video, product teaching video, or any voiced educational video from a required topic plus optional content, style, and duration requirements. Orchestrates the external remotion skill installed from google-labs-code/stitch-skills and a local configurable microsoft/VibeVoice-1.5B voice model, including voice cloning when the user provides an authorized reference voice.
---

# Teaching Video Maker

把用户的主题变成一条有旁白、有画面、有节奏的教学视频。默认输出一条带声音的 mp4，而不是只输出脚本、分镜或无声动画。

## Inputs

收集并规范化这 4 个输入：

- `视频主题`：必选。没有主题时先问用户，不要猜。
- `内容要求`：可选。可以是受众、知识点、必须覆盖/避开的内容、案例、语言、术语密度。
- `风格要求`：可选。默认 `简洁科技风`。也可以从内置风格里选择或按用户描述自定义。
- `时间要求`：可选。默认 `3分钟`。没有明确要求时按 180 秒规划。

## Built-In Styles

- `简洁科技风`（默认）：浅色或深灰背景、清晰标题、克制动效、几何图形、代码/流程图/信息卡片，适合技术教学。
- `白板手绘风`：白底、手绘线条、逐步出现的概念图，适合入门解释。
- `动态信息图风`：图表、节点、时间线、对比卡片，适合趋势、架构和数据解释。
- `产品演示风`：界面窗口、光标动作、步骤卡、局部放大，适合工具教程。
- `课堂讲解风`：讲义式排版、章节标题、例题和总结，适合课程切片。
- `故事案例风`：问题场景、角色任务、解决路径，适合用案例带动理解。

## Dependency Setup

这个 skill 依赖 Google Labs Code 的 `remotion` skill。第一次使用前，运行：

```bash
scripts/ensure_remotion_skill.sh
```

脚本会调用用户指定的命令：

```bash
npx skills add https://github.com/google-labs-code/stitch-skills --skill remotion
```

如果当前会话尚未自动加载新安装的 `remotion` skill，手动找到它的 `SKILL.md` 并按里面的 Remotion 项目创建、预览和渲染步骤执行。

这个 skill 还要求本地可用 `microsoft/VibeVoice-1.5B`。生成旁白前必须先运行：

```bash
scripts/ensure_vibevoice.sh
```

检查顺序：

1. 如果 `VIBEVOICE_ENDPOINT` 指向一个可用本地服务，直接复用。
2. 如果 `VIBEVOICE_TTS_CMD` 已配置，直接复用该命令。
3. 如果两者都没有，先在本机部署 VibeVoice 命令适配器：下载/复用 TTS 实现源码、创建 Python venv、安装依赖，并缓存 `microsoft/VibeVoice-1.5B` 权重。
4. 部署脚本会写入 `$HOME/.cache/nick-skills/vibevoice/env.sh`。在当前 shell 中 `source` 它之后再生成音频。
5. 托管部署默认写入固定 `VIBEVOICE_SPEAKER_ID=Bowen` 和 `VIBEVOICE_SEED=1227`，避免分 scene 生成时出现音色、音高或说话状态漂移。

注意：Microsoft 官方 VibeVoice 仓库在 2025-09-05 后恢复为不含 TTS 代码的说明仓库。自动部署默认使用社区保留的 VibeVoice TTS 实现加载 Microsoft 权重；如用户已有内部部署，可通过 `VIBEVOICE_ENDPOINT` 或 `VIBEVOICE_TTS_CMD` 覆盖，不要重复部署。

## Voice Engine

默认使用本地部署的 VibeVoice：

- 默认模型：`microsoft/VibeVoice-1.5B`
- 默认要求：本地推理，不使用云 TTS，除非用户明确允许
- 默认锁定 speaker 和 seed：中文 `Bowen` + `1227`；更换音色时也要为整条视频使用同一个 speaker / seed
- 支持配置不同模型、端点、命令、音色和克隆声音参考音频
- 声音克隆只在用户提供授权参考音频时使用；不要克隆公众人物、第三方或不明来源声音

配置和接入细节见 [VibeVoice integration](references/vibevoice-integration.md)。

## Output Directory

每条视频创建独立目录：

```text
teaching-video/YYYYMMDD/<topic-slug>/
  brief.md
  outline.md
  narration.md
  storyboard.md
  timing.json
  audio/
  remotion/
  output/
```

最终产物默认放在：

```text
teaching-video/YYYYMMDD/<topic-slug>/output/<topic-slug>.mp4
```

## Workflow

1. **Clarify input**：确认主题；缺失的内容要求、风格和时长使用默认值。
2. **Make a brief**：写 `brief.md`，包含受众、学习目标、内容边界、风格、总时长。
3. **Design the lesson**：写 `outline.md`，用“问题 -> 核心概念 -> 例子 -> 操作/判断 -> 总结”组织。
4. **Write narration first**：写 `narration.md`。旁白决定时间线，画面必须服务旁白。
5. **Split into scenes**：写 `storyboard.md`，每个 scene 包含旁白片段、画面内容、动效、屏幕文字和预估时长。
6. **Ensure local VibeVoice**：如果本地没有可用的 `microsoft/VibeVoice-1.5B` endpoint 或命令，先运行 `scripts/ensure_vibevoice.sh` 完成本地部署，并 `source` 它输出的 `env.sh`。
7. **Generate voice**：用本地 VibeVoice 为每个 scene 生成音频，保存到 `audio/scene-XX.wav` 或 `audio/scene-XX.mp3`。同一条视频必须使用同一个 `VIBEVOICE_SPEAKER_ID`、`VIBEVOICE_SEED`、`VIBEVOICE_CFG_SCALE` 和 voice reference。
8. **Check voice consistency**：运行 `scripts/check_audio_consistency.py audio`，并快速试听每个 scene 的开头。若某段音色或音调明显不同，保留同一 speaker / seed 重新生成该 scene，或重新生成全套音频。
9. **Measure audio**：用 `ffprobe` 读取每段真实时长，生成 `timing.json`。不要只依赖估算时长。
10. **Build Remotion video**：调用 `remotion` skill 创建或更新 `remotion/` 项目，按 `timing.json` 编排画面和 `<Audio>`。
11. **Preview and fix sync**：用 Remotion preview 或 render 检查音画对应。旁白提到的概念，应在 0.5 秒内出现在画面上。
12. **Render final video**：渲染有声 mp4 到 `output/`。

## Duration Rules

- 默认 3 分钟，目标总时长 170 到 190 秒。
- 中文旁白初稿按每分钟约 240 到 280 个汉字估算；英文按每分钟约 130 到 160 个词估算。
- 真正时间线以 VibeVoice 生成后的音频时长为准。
- 如果音频总时长偏离目标超过 10%，先改旁白，再重新生成音频，不要只拉伸视频。
- 教学视频宁可少讲一个点，也不要把语速压得不自然。

## Script Rules

- 开头 5 到 10 秒说明“学完能做什么”。
- 每 20 到 35 秒切一个 scene，避免长时间静态画面。
- 每个 scene 只讲一个小知识点。
- 屏幕文字只放关键词、公式、命令、步骤名，不要把整段旁白搬上屏幕。
- 结尾必须有 15 秒以内的总结和下一步行动。
- 语音和视频内容必须对应：旁白说到的步骤、对象、代码、图形或结论，要在当前 scene 中同步出现。

## Remotion Rules

使用外部 `remotion` skill 负责项目搭建、组件实现、预览和渲染。对教学视频，额外遵守：

- 用 `timing.json` 驱动画面，不要写散落在组件里的硬编码时间。
- 每个 scene 应有稳定的 `id`、`startSec`、`durationSec`、`audioFile`、`visuals`。
- 音频用 Remotion 的 `<Audio>` 放到对应 scene，避免后期手动拼接造成漂移。
- 动效要解释内容，避免无意义炫技。
- 最终必须渲染带声音的视频文件。

完整编排契约见 [Remotion teaching workflow](references/remotion-teaching-workflow.md)。

## Quality Gate

完成前检查：

- 已运行或确认安装 `remotion` skill。
- 已运行 `scripts/ensure_vibevoice.sh`，或确认 `VIBEVOICE_ENDPOINT` / `VIBEVOICE_TTS_CMD` 指向可用的本地 `microsoft/VibeVoice-1.5B` 部署。
- 同一条视频的所有 scene 使用同一个 speaker、seed、cfg scale 和 voice reference；不要让异常 scene 用随机 seed 单独生成。
- `brief.md`、`outline.md`、`narration.md`、`storyboard.md`、`timing.json` 存在。
- 每个 scene 都有对应音频文件。
- 已运行 `scripts/check_audio_consistency.py audio`，且已试听确认没有明显音色或音调跳变。
- `timing.json` 的总时长接近用户要求。
- 视频画面根据真实音频时长编排，而不是只按估算时长。
- 旁白里的关键概念都在相邻画面出现。
- 最终 `output/<topic-slug>.mp4` 有音轨，且可以播放。

## Final Response

向用户返回：

- 视频文件路径
- 实际总时长
- 使用的风格
- 使用的 VibeVoice 配置摘要，例如模型、端点或命令、是否使用克隆声音
- 如未能生成最终 mp4，明确说明卡在哪一步，并保留已生成的脚本、音频或 Remotion 项目路径
