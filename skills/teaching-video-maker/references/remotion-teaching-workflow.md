# Remotion Teaching Workflow

Use the external `remotion` skill for project creation, component work, preview, and rendering. This reference defines the teaching-video contract around it.

## Install Dependency

Run from the skill directory or repo root:

```bash
npx skills add https://github.com/google-labs-code/stitch-skills --skill remotion
```

## Files to Create

Inside `teaching-video/YYYYMMDD/<topic-slug>/`:

- `brief.md`：topic, audience, objectives, style, duration
- `outline.md`：lesson structure
- `narration.md`：scene-by-scene voiceover text
- `storyboard.md`：scene visuals and animation notes
- `timing.json`：machine-readable timing contract
- `audio/scene-XX.wav`：VibeVoice output
- `remotion/`：Remotion project
- `remotion/public/audio/scene-XX.wav`：copy of scene audio for Remotion `staticFile()`
- `output/<topic-slug>.mp4`：final voiced video

## timing.json Shape

```json
{
  "fps": 30,
  "width": 1920,
  "height": 1080,
  "style": "简洁科技风",
  "targetDurationSec": 180,
  "actualDurationSec": 176.4,
  "scenes": [
    {
      "id": "scene-01",
      "title": "开场：学完能做什么",
      "startSec": 0,
      "durationSec": 14.2,
      "audioFile": "audio/scene-01.wav",
      "narration": "这段旁白文本",
      "visuals": [
        "大标题",
        "三个学习收益卡片",
        "轻微推入动效"
      ],
      "onScreenText": [
        "3 分钟理解核心流程"
      ]
    }
  ]
}
```

## Sync Rules

- Use measured audio durations to calculate `startSec`.
- Convert seconds to frames with `Math.round(sec * fps)`.
- Put each scene in a Remotion `<Sequence>` whose duration matches the measured audio.
- Copy scene audio into `remotion/public/audio/` and place it inside the same `<Sequence>` using `<Audio src={staticFile(scene.audioFile)} />`.
- Do not pass `../audio/...` or other relative paths to `staticFile()`; Remotion only serves files from `public/`.
- Visual text should appear no later than 0.5 seconds after the corresponding narration phrase.
- If an animation needs extra reading time, add silence or rewrite narration; do not make visuals lag behind speech.

## Visual Rules

- Build actual teaching visuals: diagrams, steps, examples, code snippets, UI mockups, timelines, or comparison cards.
- Do not fill the video with decorative gradients only.
- Use one main idea per scene.
- Keep screen text brief enough to read in the scene duration.
- Reserve the final scene for recap and next action.

## Render Checks

Before final response:

```bash
ffprobe -v error -show_entries stream=codec_type -of csv=p=0 output/<topic-slug>.mp4
```

The output must include both `video` and `audio` streams.

## Reference

- Remotion skill listing: https://skills.sh/google-labs-code/stitch-skills/remotion
