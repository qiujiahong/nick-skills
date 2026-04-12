# CH Dialogue Workflow

Use this reference when building a countryhuman / CH-style voiced dialogue video.

## Story Shape

Prefer three acts. For a one-minute video, keep each act to 2 or 3 tight lines; for a 3-minute video, use 5 to 7 lines per act.

1. `需求`：who wants what, what pressure created the need, and what the constraint is.
2. `行动`：how the deal, plan, experiment, or confrontation unfolds.
3. `复盘`：what changed, who reacted, and what the viewer should remember.

The act/task fields are production structure only. Characters should not say `任务一`, `任务二`, or `任务三`; write the dialogue as a compact story conversation.

For historical and geopolitical stories, keep the spine factual and let humor come from character contrast, not from inventing facts.

## Character Handling

- `兔子`：usually represents China. Use concise, pragmatic lines. Avoid triumphalist or dehumanizing language.
- `骆驼`：usually represents Saudi Arabia or Gulf interests. Emphasize security needs, bargaining position, and sovereignty.
- `鹰酱`：usually represents the United States. Use surprise, alliance-management concerns, export-control logic, or regional-balance framing.
- Add visual animal traits sparingly: rabbit ears, camel hump/ears, eagle beak/sunglasses. The head should still read as CH / countryhuman.
- If the user says not to write country names explicitly, keep those names out of role labels, act titles, fact labels, subtitles, and publish copy. Use aliases such as `东边卖家`, `海湾买家`, `保护伞`, `第二家店`, or `华府`.

## Dialogue Rules

- One speaker per line.
- Keep most lines between 25 and 55 Chinese characters for readable timing.
- Give every act a mini-turn: setup, pushback, answer, consequence.
- Do not use narration unless the user asks for it. If context is needed, put it into a character's line or the on-screen fact label.
- Mark uncertain details with softer language: `公开资料称`, `外界报道`, `据称`, `后来被公开展示`.
- Keep task titles, task objectives, fact labels, captions, and publish copy in Chinese by default.
- Use `spokenText` when subtitles contain English abbreviations, missile designations, or numbers that should be read naturally in Chinese.

## Visual Rules

- Use a stable three-character layout so viewers can track the speakers.
- Highlight the active speaker with a ring, stage light, or nameplate.
- Default final output should be animated: active speaker body bob, hand gesture, mouth change, and blink. Use static frames only for drafts or explicit fallback.
- Put the current line in a large speech bubble and keep it under 3 wrapped rows when possible.
- Use the act title and one key fact at the top of the screen.
- Use a CH humanoid look inspired by common countryhuman references: white hair, flag face, slim upper body, clothing silhouette, and small identity accessories. Avoid default countryball round-head animal styling unless the user asks for it.
- Avoid military gore, real injury, hate symbols, or celebration of real-world violence.

## Fact Notes

For real events, create `sources.md` with:

- Source title and URL.
- The fact used in the script.
- Any uncertainty or disputed number.

When the exact number, year, or motivation varies by source, avoid a single hard number in dialogue unless the user explicitly wants a cited documentary style.

## Local Rendering Notes

Use `scripts/render_countryhuman_dialogue.py` for deterministic local output. The default voice engine is local `voice-tts` / VibeVoice for more human-like Chinese voices:

```bash
python3 skills/countryhuman-video-maker/scripts/render_countryhuman_dialogue.py \
  --input countryhuman-video/YYYYMMDD/<slug>/dialogue.json \
  --output-root countryhuman-video
```

The renderer generates animated SVG frames, converts them with macOS `sips`, synthesizes local speech with `voice-tts`, and assembles the mp4 with `ffmpeg`. Use `--voice-engine say` only as a low-quality fallback. Add `--static` only for quick drafts; adjust motion smoothness with `--animation-fps`.

When only captions, visual copy, or planned `durationSec` values changed, pass `--reuse-audio` to keep existing `audio/line-XX-vibevoice.wav` files and avoid regenerating every voice line.
