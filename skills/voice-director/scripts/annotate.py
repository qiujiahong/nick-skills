#!/usr/bin/env python3
"""
语音导演：用 LLM 为台词自动标注情感、语速、语调标记。
输出格式兼容 voice-tts 的分段模式。
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("Error: requests library required.", file=sys.stderr)
    sys.exit(1)

SYSTEM_PROMPT = """你是一位专业的语音导演。你的任务是为给定的台词/文本添加语音情感标记，让 TTS 合成出有表现力的语音。

## 可用标记格式

用 [参数] 和 [/] 包裹文本段落：
[emotion=xxx speed=x.x pitch=x.x]文本内容[/]

## 可用参数

### emotion（情感，可选）
- happy — 开心、愉快、兴奋
- sad — 悲伤、低落、感伤
- angry — 生气、愤怒、不满
- scare — 恐惧、害怕、紧张
- surprise — 惊讶、意外
- hate — 厌恶、反感
- neutral — 中性、平静

### speed（语速，可选，0.5~2.0）
- 0.6~0.8 — 缓慢、沉重、深情
- 0.9~1.0 — 正常
- 1.1~1.3 — 轻快、急切
- 1.4~1.8 — 急促、紧张

### pitch（语调，可选，0.5~2.0）
- 0.7~0.9 — 低沉、深沉、严肃
- 1.0 — 正常
- 1.1~1.3 — 高昂、明快、激动

## 规则

1. 根据文本的语境和情感自然地分段，不要机械地逐句标记
2. 平淡的叙述段落不需要标记，保持自然
3. 情感转折处要分段
4. 对话内容根据说话人的情绪标记
5. 参数不需要全部指定，只标注有变化的参数
6. speed 和 pitch 用一位小数，如 1.2 而非 1.20
7. 保持原文内容不变，只添加标记
8. emotion 只能用以下 7 个值：happy、sad、angry、scare、surprise、hate、neutral。禁止使用其他值（如 serious、confident、deceptive 等无效）
9. 想表达严肃/紧张/神秘等情绪时，通过 speed 和 pitch 组合实现，不要编造 emotion 值

## 输出

只输出标注后的文本，不要加任何解释。"""


def annotate(text: str, api_key: str, base_url: str, model: str) -> str:
    """Use LLM to annotate text with emotion markers."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请为以下文本添加语音情感标记：\n\n{text}"},
        ],
        "temperature": 0.7,
    }

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )

    if resp.status_code != 200:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        print(resp.text[:500], file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    return result["choices"][0]["message"]["content"].strip()


def main():
    parser = argparse.ArgumentParser(description="语音导演 - 自动标注台词情感")
    parser.add_argument("text", nargs="?", default=None, help="要标注的文本")
    parser.add_argument("-f", "--file", default=None, help="从文件读取文本")
    parser.add_argument("-o", "--output", default=None, help="输出到文件")
    parser.add_argument("--model", default=None, help="LLM 模型名称")
    parser.add_argument("--base-url", default=None, help="API base URL")
    parser.add_argument("--api-key", default=None, help="API key")

    args = parser.parse_args()

    # Get text
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("Error: no text provided", file=sys.stderr)
        sys.exit(1)

    # API config
    api_key = args.api_key or os.environ.get("NICK_SKILLS_ENV_DIRECTOR_API_KEY") \
              or os.environ.get("ARK_API_KEY")
    base_url = args.base_url or os.environ.get("NICK_SKILLS_ENV_DIRECTOR_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model = args.model or os.environ.get("NICK_SKILLS_ENV_DIRECTOR_MODEL", "doubao-1-5-pro-32k-250115")

    if not api_key:
        print("Error: No API key. Set NICK_SKILLS_ENV_DIRECTOR_API_KEY or ARK_API_KEY", file=sys.stderr)
        sys.exit(1)

    print(f"Annotating text ({len(text)} chars) with {model}...", file=sys.stderr)

    result = annotate(text, api_key, base_url, model)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Saved to: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
