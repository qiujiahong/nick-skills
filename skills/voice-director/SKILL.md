---
name: voice-director
description: 语音导演 — 用 AI 为台词自动标注情感、语速、语调标记。当用户提供纯文本台词并希望生成有表现力的语音时，先用此 skill 标注，再交给 voice-tts 合成。
---

# 语音导演 (Voice Director)

用 LLM 分析文本的情感和节奏，自动添加分段标记。注意：当前 `voice-tts` 默认使用本地 VibeVoice，不调用远程 TTS；这些标记主要用于保留导演意图，`voice-tts` 合成时会默认去掉不支持的标记并保留文本。

## 环境变量

- `NICK_SKILLS_ENV_DIRECTOR_API_KEY` — LLM API Key（可选，会 fallback 到 `ARK_API_KEY`）
- `NICK_SKILLS_ENV_DIRECTOR_BASE_URL` — API 地址（默认：豆包 Ark）
- `NICK_SKILLS_ENV_DIRECTOR_MODEL` — 模型名称（默认：`doubao-1-5-pro-32k-250115`）

## 使用方法

```bash
# 直接传文本
python3 scripts/annotate.py "你的台词文本"

# 从文件读取
python3 scripts/annotate.py -f story.txt

# 输出到文件
python3 scripts/annotate.py "台词" -o annotated.txt

# 从 stdin 读取
echo "台词内容" | python3 scripts/annotate.py
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `text` | 要标注的文本 | — |
| `-f, --file` | 从文件读取 | — |
| `-o, --output` | 输出到文件 | 输出到 stdout |
| `--model` | LLM 模型 | 环境变量或 `doubao-1.5-pro-256k` |
| `--base-url` | API 地址 | 环境变量或豆包 Ark |
| `--api-key` | API Key | 环境变量 |

## 输出格式

输出带有情感标记的文本。交给本地 `voice-tts` 时，默认会去掉标记并合成文本内容：

```
[emotion=happy speed=1.1 pitch=1.2]太棒了！今天天气真好！[/]
可是天色渐渐暗了下来。
[emotion=scare speed=0.8 pitch=0.9]突然，远处传来一阵奇怪的声音。[/]
```

## 标记说明

| 参数 | 值 | 含义 |
|------|-----|------|
| `emotion` | happy/sad/angry/scare/hate/surprise/neutral | 情感 |
| `speed` | 0.5~2.0 | 语速 |
| `pitch` | 0.5~2.0 | 语调高低 |

## 与 voice-tts 配合使用

### 两步走工作流

```bash
# 第 1 步：用 voice-director 标注情感
python3 voice-director/scripts/annotate.py -f story.txt -o annotated.txt

# 第 2 步：用本地 voice-tts 合成语音
python3 voice-tts/scripts/tts.py "$(cat annotated.txt)" --output story.mp3
```

### Agent 使用流程

1. 用户提供纯文本台词
2. 调用 `voice-director/scripts/annotate.py` 获取标注后的文本
3. 将标注文本传给 `voice-tts/scripts/tts.py` 生成语音
4. 发送音频给用户

## 示例

输入：
```
妈妈出门前说：谁来敲门都不要开！天黑了，有人敲门说：我是外婆呀！小毛就把门打开了。进来的哪是什么外婆，是一只大灰狼！
```

输出：
```
妈妈出门前说：[emotion=neutral speed=0.9]谁来敲门都不要开！[/]
天黑了，有人敲门说：[pitch=0.8 speed=0.9]我是外婆呀！[/]
小毛就把门打开了。
[emotion=scare speed=0.8 pitch=0.9]进来的哪是什么外婆，是一只大灰狼！[/]
```
