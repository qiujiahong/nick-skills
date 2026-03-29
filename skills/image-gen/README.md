# image-gen

AI 图像生成 Skill，基于 Gemini Flash Image Preview 模型，支持：

- 文生图
- 图生图
- 多图输入
- 多比例
- 多分辨率

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
IMAGE_GEN_API_KEY=your-api-key
IMAGE_GEN_BASE_URL=https://api.apiyi.com
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
IMAGE_GEN_ASPECT_RATIO=16:9
IMAGE_GEN_IMAGE_SIZE=2K
```

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
- `2K`
- `4K`

## 用法

### 文生图

```bash
python3 scripts/generate_image.py \
  "一只可爱的柴犬坐在樱花树下，水彩画风格" \
  --aspect-ratio 16:9 \
  --image-size 2K \
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

## License

MIT
