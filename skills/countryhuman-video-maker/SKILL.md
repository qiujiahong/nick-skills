---
name: countryhuman-video-maker
description: 生成 CH / countryhuman 风格的有声对话视频。Use when the user asks to create a countryhuman, CH, countryball-human hybrid, geopolitical character dialogue, historical/political explainer skit, or voiced multi-character dialogue video with roles such as 兔子、骆驼、鹰酱. Produces script, storyboard, timed local voiceover, rendered mp4, and publish-ready summary.
---

# Countryhuman Video Maker

把一个历史、地缘、商业或科技故事改写成 CH 风格角色对话视频。默认目标是输出一条带配音的 mp4，而不是只给脚本或分镜。

## Inputs

收集并规范化这些输入：

- `视频主题`：必选。没有主题时先问用户，不要猜。
- `角色`：可选。默认按用户命名；常见预设包括 `兔子`、`骆驼`、`鹰酱`。
- `对话结构`：可选。默认 3 个任务 / 3 幕，每幕 50 到 70 秒。
- `时间要求`：可选。默认 3 分钟，目标 170 到 190 秒。
- `事实要求`：可选。涉及真实历史、现代政治、军工、金融或医疗法律内容时，先核实关键事实。
- `配音要求`：可选。默认本地配音，不调用远程 TTS API。

## Output Directory

每条视频创建独立目录：

```text
countryhuman-video/YYYYMMDD/<topic-slug>/
  brief.md
  dialogue.json
  script.md
  storyboard.md
  timing.json
  sources.md
  audio/
  frames/
  segments/
  output/
    <topic-slug>.mp4
    <topic-slug>-summary.md
```

## Workflow

1. **Clarify the premise**：确认主题、角色、时长、语言和敏感边界。
2. **Verify the spine**：真实事件至少核实年份、主体、冲突点和后果。把链接或资料摘要写进 `sources.md`。
3. **Write the 3-task arc**：用“需求 -> 交易/行动 -> 后果/复盘”或用户指定结构拆成 3 幕。
4. **Write dialogue first**：每句只让一个角色说话；角色观点要清楚但避免现实人群标签化。
5. **Create `dialogue.json`**：按下面 schema 写入角色、任务、台词、计划时长和发布文案。
6. **Render locally**：运行 `scripts/render_countryhuman_dialogue.py` 生成配音、画面、时间线和 mp4。
7. **Quality gate**：检查总时长、音轨、画面、字幕和事实表述。

## Dialogue Schema

把输入写成 UTF-8 JSON：

```json
{
  "title": "沙特买东风导弹的故事",
  "slug": "saudi-dongfeng-dialogue",
  "targetDurationSec": 180,
  "style": "CH(countryhuman)地缘对话",
  "characters": [
    {"id": "rabbit", "name": "兔子", "role": "中国", "voice": "Tingting"},
    {"id": "camel", "name": "骆驼", "role": "沙特", "voice": "Meijia"},
    {"id": "eagle", "name": "鹰酱", "role": "美国", "voice": "Sinji"}
  ],
  "tasks": [
    {"id": "task-1", "title": "任务一：提出需求", "objective": "解释为什么要找远程威慑"},
    {"id": "task-2", "title": "任务二：完成交易", "objective": "解释秘密采购与外界曝光"},
    {"id": "task-3", "title": "任务三：复盘影响", "objective": "解释地区平衡和后续影响"}
  ],
  "dialogue": [
    {"task": "task-1", "speaker": "camel", "text": "台词", "durationSec": 9.0}
  ],
  "summary": {
    "title": "16字以内标题",
    "copy": "60到120字发布文案。",
    "hashtags": ["#冷战往事", "#地缘故事"]
  }
}
```

每句 `durationSec` 是目标画面长度。脚本会用真实音频长度覆盖过短的计划时长，并在音频较短时补静音，保证总时长接近目标。

## Local Render

从仓库根目录运行：

```bash
python3 skills/countryhuman-video-maker/scripts/render_countryhuman_dialogue.py \
  --input countryhuman-video/YYYYMMDD/<slug>/dialogue.json \
  --output-root countryhuman-video \
  --voice-engine say
```

脚本依赖：

- `ffmpeg` / `ffprobe`
- macOS `say` 和 `sips`，用于本地配音和 SVG 转 PNG
- Python 标准库；不需要 Pillow、moviepy 或远程视频 API

如果用户明确要求更拟人的音色，先尝试 `voice-tts` skill 生成每句 wav，再把音频路径写进 `dialogue[].audioFile`，或改脚本接入本地 `voice-tts/scripts/tts.py`。不要把台词发到远程 TTS。

## Style Rules

- CH 是拟人化叙事外壳，不是现实群体评价。让角色代表国家/机构立场，避免攻击民族、宗教或普通民众。
- 兔子、骆驼、鹰酱等网络代称可以使用，但画面和台词要保持讽刺克制。
- 屏幕文字只放任务名、关键事实和当前台词，不要把资料全文塞进画面。
- 每 6 到 12 秒换一张画面；每幕至少让 2 个角色发言。
- 事实表达用“据公开资料”“外界报道”“后来公开展示”等措辞，避免把未证实细节说成定论。

更详细的编剧、分镜、事实和角色规则见 [CH dialogue workflow](references/ch-dialogue-workflow.md)。

## Quality Gate

完成前检查：

- `dialogue.json`、`script.md`、`storyboard.md`、`timing.json` 存在。
- `sources.md` 覆盖真实事件的关键事实。
- `output/<slug>.mp4` 有 video 和 audio 两条 stream。
- 实际总时长在用户要求的 10% 范围内；3 分钟默认接受 170 到 190 秒。
- 三个角色都至少有 3 句台词；每个任务 / 幕都有明确冲突和小结。
- 画面能看出 CH / countryhuman 风格：角色拟人、头部带国别符号、当前说话者高亮。
- 最终总结文案短到可直接发朋友圈 / 视频号。

## Final Response

向用户返回：

- 视频文件路径
- 发布总结路径
- 实际总时长
- 角色和本地配音方式
- 使用的事实来源摘要
- 如果未能生成 mp4，明确说明卡在哪一步，并保留已生成脚本、音频或画面路径
