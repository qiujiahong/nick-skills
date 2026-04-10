---
name: image-gen
description: AI图像生成与编辑。支持文生图、图生图、多图输入、风格转换。当用户要求画图、生成图片、参考图改图、合成多张参考图、图片风格转换时使用此 skill。支持比例：1:1、1:4、4:1、1:8、8:1、2:3、3:2、3:4、4:3、4:5、5:4、9:16、16:9、21:9；支持分辨率：standard、2K、4K。
---

# AI 图像生成

通过执行脚本调用 Gemini Flash Image Preview API 生成图片。

支持三种模式：

- **文生图**：只有提示词
- **图生图**：1 张参考图 + 提示词
- **多图输入**：多张参考图 + 提示词

## 环境变量

脚本通过以下环境变量获取 API 配置：

- `IMAGE_GEN_API_KEY` — API 密钥
- `IMAGE_GEN_BASE_URL` — API 基础地址（默认：`https://api.apiyi.com`）
- `IMAGE_GEN_MODEL` — 默认模型（默认：`gemini-3.1-flash-image-preview`）
- `IMAGE_GEN_ASPECT_RATIO` — 默认宽高比（默认：`16:9`）
- `IMAGE_GEN_IMAGE_SIZE` — 默认图片尺寸（默认：`2K`）
- `IMAGE_GEN_API_STYLE` — API 请求格式，可选 `gemini` 或 `xheai`；不设置时，如果 `IMAGE_GEN_BASE_URL` 包含 `xheai` 会自动使用 `xheai`

说明：

- `gemini` 格式走 `/v1beta/models/<model>:generateContent`，使用 Gemini 原生字段
- `xheai` 格式下，文生图走 `/v1/images/generations`
- `xheai` 格式下，图生图 / 多图编辑走 `/v1/images/edits`
- `xheai` 会统一解析 OpenAI 风格返回里的 `data[0].url` 或 `data[0].b64_json`

## 使用方法

### 1) 文生图

```bash
export IMAGE_GEN_API_KEY="your-api-key"
export IMAGE_GEN_BASE_URL="https://api.apiyi.com"

python3 scripts/generate_image.py "一只可爱的柴犬坐在樱花树下，水彩画风格" \
  --model gemini-3.1-flash-image-preview \
  --aspect-ratio 16:9 \
  --image-size 2K \
  --output output.png
```

### 2) 图生图

```bash
python3 scripts/generate_image.py "保留主体构图，改成吉卜力风格，色彩更柔和" \
  --input-image reference.png \
  --aspect-ratio 3:4 \
  --image-size 2K \
  --output output.png
```

### 3) 多图输入

```bash
python3 scripts/generate_image.py "结合这几张参考图的构图、服装和配色，生成一张统一风格的新海报" \
  --input-image ref1.png \
  --input-image ref2.jpg \
  --input-image ref3.webp \
  --aspect-ratio 4:5 \
  --image-size 2K \
  --output output.png
```

## 参数说明

- `prompt`（必填）：图片描述提示词
- `--model, -m`：模型名称，默认 `gemini-3.1-flash-image-preview`
- `--output, -o`：输出文件路径，默认当前目录 `generated_image.<ext>`
- `--aspect-ratio`：图片比例
- `--image-size`：图片尺寸，支持 `standard`、`2K`、`4K`
- `--input-image`：输入参考图路径，可重复传多次

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

## 支持的尺寸

- `standard`
- `2K`
- `4K`

## 工作流程

1. **理解需求**：判断是文生图、图生图，还是多图融合
2. **确定比例和尺寸**：根据用途选择合适的 `aspectRatio` 与 `imageSize`
3. **组织提示词**：明确主体、风格、构图、颜色和参考约束
4. **执行脚本**：调用 `scripts/generate_image.py`
5. **校验结果**：确认生成文件存在、格式正常
6. **按需上传**：若要发到飞书，再上传图片并发送

## 提示词技巧

### 文生图
- 描述主体、场景、风格、光线、镜头感
- 明确色调和构图要求

### 图生图
- 说明“保留什么、修改什么”
- 比如：保留姿势、改风格；保留构图、换服装；保留角色、换背景

### 多图输入
- 明确每张图分别提供什么参考
- 比如：
  - 图 1 参考构图
  - 图 2 参考服装
  - 图 3 参考色调

## 示例

### 宽幅海报

```bash
python3 scripts/generate_image.py \
  "赛博朋克风格的未来城市夜景，霓虹灯、雨夜、电影感构图，高细节" \
  --aspect-ratio 21:9 \
  --image-size 2K \
  --output cyberpunk-poster.png
```

### 超长横幅

```bash
python3 scripts/generate_image.py \
  "极简科技感官网横幅，蓝白配色，大量留白，未来感 UI 背景" \
  --aspect-ratio 8:1 \
  --image-size standard \
  --output hero-banner.png
```

### 参考图改风格

```bash
python3 scripts/generate_image.py \
  "保留原始人物姿势与主体布局，改成水彩插画风，柔和暖色调" \
  --input-image portrait.jpg \
  --aspect-ratio 3:4 \
  --image-size 2K \
  --output watercolor-portrait.png
```
