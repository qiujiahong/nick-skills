---
name: wechat-mp-publisher
description: 自动发布微信公众号文章。支持通过微信公众号接口上传封面图、上传正文图片、把 Markdown 美化为适合公众号的 HTML、创建草稿，并可选择提交发布。凭证可从本地 `.env` 自动加载。
metadata:
  openclaw:
    os: [darwin, linux]
    requires:
      bins: [python3]
---

# WeChat MP Publisher

这个 skill 用微信公众号接口自动发布文章，默认走“先建草稿，再决定是否发布”的稳妥流程。

## 适用场景

- 用户要把一篇文章发到微信公众号
- 用户提供标题、作者、摘要、封面图、正文
- 用户希望自动创建公众号草稿
- 用户明确要求时，再执行发布动作

## 环境变量

需要先配置公众号接口凭证。脚本会优先自动读取当前 skill 目录下的 `.env.local` 和 `.env`。

必要变量：

- `WECHAT_MP_APP_ID`
- `WECHAT_MP_APP_SECRET`

可选：

- `WECHAT_MP_THUMB_MEDIA_ID` — 默认封面 media_id
- `WECHAT_MP_AUTHOR` — 默认作者名
- `WECHAT_MP_BASE_URL` — 默认 `https://api.weixin.qq.com/cgi-bin`
- `WECHAT_MP_BASE_URL_PROXY` — 如果设置了这个值，则优先通过代理地址和微信接口通讯

## 工作流程

1. 整理文章内容：标题、作者、摘要、封面图、正文
2. 如果正文是 Markdown，先转成适合公众号的 HTML
3. 正文里如果引用本地图片，先上传为公众号正文可用图片 URL
4. 如果只有本地封面图，先上传并拿到 `thumb_media_id`
5. 调用脚本获取 access token
6. 创建草稿
7. 只有在用户明确要求“直接发布”时，才调用发布接口
8. 返回草稿 ID / publish_id / 状态信息

## 安全规则

- 默认只创建草稿，不直接发布
- 真正对外发布前，最好给用户看一眼标题、摘要和封面
- 不要擅自替用户发文
- 正文图片和封面图上传成功后，再创建草稿，避免草稿里留下本地路径

## 使用方式

### 创建草稿

```bash
python3 scripts/wechat_mp_publish.py create-draft \
  --title "用 OpenClaw 自动化技能开发" \
  --author "Nick" \
  --digest "这是一篇介绍 OpenClaw skills 的文章" \
  --content-file article.html \
  --thumb-file ./assets/封面图-20260411-053407.png
```

### 直接从 Markdown 创建草稿

```bash
python3 scripts/wechat_mp_publish.py create-draft \
  --title "用 OpenClaw 自动化技能开发" \
  --content-file article.md \
  --content-format markdown \
  --thumb-file ./assets/封面图-20260411-053407.png \
  --rendered-html-output ./dist/article-rendered.html
```

### 只渲染，不发布

```bash
python3 scripts/wechat_mp_publish.py render-content \
  --content-file article.md \
  --content-format markdown \
  --output ./dist/article-rendered.html
```

### 单独上传正文图片

```bash
python3 scripts/wechat_mp_publish.py upload-article-image \
  --file ./assets/配图1-20260411-053407.png
```

### 单独上传封面图

```bash
python3 scripts/wechat_mp_publish.py upload-thumb-image \
  --file ./assets/封面图-20260411-053407.png
```

### 发布草稿

```bash
python3 scripts/wechat_mp_publish.py publish --media-id <MEDIA_ID>
```

### 查询发布状态

```bash
python3 scripts/wechat_mp_publish.py get-publish-status --publish-id <PUBLISH_ID>
```

## 说明

- `create-draft`：创建公众号草稿
- `render-content`：本地把 Markdown / HTML 渲染成公众号风格 HTML，便于预览
- `upload-article-image`：上传正文图片，返回可用于文章 HTML 的 URL
- `upload-thumb-image`：上传封面图，返回 `thumb_media_id`
- `publish`：提交发布草稿
- `get-publish-status`：查询发布进度
- Markdown 会先做基础美化，再转成更适合公众号阅读的 HTML
- Markdown 列表发布前会渲染为带项目符号/序号的段落，而不是原生 `<ul>/<ol>/<li>`，避免公众号编辑器把空行或列表间距重排成空圆点
- 如果 Markdown 里是本地图片路径，脚本会先上传，再替换成公众号可访问的图片 URL
- `rendered-html-output` 可把最终发送给公众号的 HTML 落盘，方便人工预览
