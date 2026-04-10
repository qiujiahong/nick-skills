# image-gen

AI 图像生成 Skill，支持 Gemini 原生接口和 xheai 代理接口，支持：

- 文生图
- 图生图
- 多图输入
- 多比例
- 多分辨率

可选代理：<https://api.xheai.cc/register?aff=TmKE>

## 安装

### OpenClaw

```bash
# ClawHub 安装（推荐）
clawhub install ai-image-gen

# Git 直接安装
cd /path/to/your/workspace/skills
git clone git@github.com:qiujiahong/image-gen.git ai-image-gen
```

### Claude Code

```bash
cd ~/.claude/skills
git clone git@github.com:qiujiahong/image-gen.git ai-image-gen
```

### OpenCode

```bash
cd ~/.opencode/skills
git clone git@github.com:qiujiahong/image-gen.git ai-image-gen
```

## 环境变量配置

使用前需配置以下环境变量（不要硬编码到代码中）：

```bash
IMAGE_GEN_API_KEY=sk-xxxxx
IMAGE_GEN_BASE_URL=https://api.xheai.cc
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
IMAGE_GEN_ASPECT_RATIO=16:9
IMAGE_GEN_IMAGE_SIZE=1k
IMAGE_GEN_API_STYLE=xheai
```

说明：

- `IMAGE_GEN_API_STYLE=gemini`：走 Gemini 原生接口 `/v1beta/models/<model>:generateContent`
- `IMAGE_GEN_API_STYLE=xheai`：文生图走 `/v1/images/generations`
- `IMAGE_GEN_API_STYLE=xheai`：图生图 / 多图编辑走 `/v1/images/edits`
- 不设置 `IMAGE_GEN_API_STYLE` 时，如果 `IMAGE_GEN_BASE_URL` 包含 `xheai`，脚本会自动使用 `xheai`
- 本地验证过 `xheai + gemini-3.1-flash-image-preview + image_size=1k` 可用；`nano-banana-2` 可能会遇到上游分组拥堵，可按需重试或切回 `gemini-3.1-flash-image-preview`

## 支持的比例

- `1:1`
- `1:4`
- `4:1`
- `1:8`
- `8:1`
- `2:3`
- `3:2`
- `3:4`
- `4:3`
- `4:5`
- `5:4`
- `9:16`
- `16:9`
- `21:9`

## 支持的分辨率

- `standard`
- `1k`
- `2K`
- `4K`

## 用法

### 文生图

```bash
python3 scripts/generate_image.py \
  "一只可爱的柴犬坐在樱花树下，水彩画风格" \
  --aspect-ratio 16:9 \
  --image-size 1k \
  --output output.png
```

### 图生图

```bash
python3 scripts/generate_image.py \
  "保留主体构图，改成吉卜力风格，色彩更柔和" \
  --input-image reference.png \
  --aspect-ratio 3:4 \
  --image-size 2K \
  --output output.png
```

### 多图输入

```bash
python3 scripts/generate_image.py \
  "结合这几张参考图的构图、服装和配色，生成一张统一风格的新海报" \
  --input-image ref1.png \
  --input-image ref2.jpg \
  --input-image ref3.webp \
  --aspect-ratio 4:5 \
  --image-size 2K \
  --output output.png
```

## 参数

- `prompt`：提示词
- `--model`：模型名，默认 `gemini-3.1-flash-image-preview`
- `--aspect-ratio`：比例
- `--image-size`：尺寸
- `--input-image`：输入图，可重复使用
- `--output`：输出文件路径

## 默认模型

- `gemini-3.1-flash-image-preview`

如果使用 xheai，推荐先用：

```bash
python3 scripts/generate_image.py \
  "清新手绘风技术博客插图，浅色背景，柔和蓝绿色，少文字，无水印" \
  --model gemini-3.1-flash-image-preview \
  --aspect-ratio 16:9 \
  --image-size 1k \
  --output output.png
```

## License

MIT
