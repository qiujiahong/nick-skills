# wechat-mp-publisher

微信公众号自动发文 skill。

## 当前能力

- 自动读取 `skills/wechat-mp-publisher/.env` 或 `.env.local`
- 获取公众号 `access_token`
- 上传正文图片并返回文章可用 URL
- 上传封面图并返回 `thumb_media_id`
- 创建草稿（draft/add）
- 提交发布（freepublish/submit）
- 查询发布状态（freepublish/get）
- 支持 HTML / Markdown 正文输入
- Markdown 会转换成更适合公众号阅读的 HTML

## 环境变量

可以直接写到 `skills/wechat-mp-publisher/.env`：

```bash
WECHAT_MP_APP_ID="wx123..."
WECHAT_MP_APP_SECRET="abcdef..."
WECHAT_MP_AUTHOR="Nick"
WECHAT_MP_THUMB_MEDIA_ID="MEDIA_ID"
```

## 用法

创建草稿：

```bash
python3 scripts/wechat_mp_publish.py create-draft \
  --title "我的第一篇自动发文测试" \
  --content-file article.md \
  --content-format markdown \
  --thumb-file ./assets/封面图-20260411-053407.png \
  --rendered-html-output ./dist/article-rendered.html
```

本地渲染公众号 HTML：

```bash
python3 scripts/wechat_mp_publish.py render-content \
  --content-file article.md \
  --content-format markdown \
  --output ./dist/article-rendered.html
```

上传正文图片：

```bash
python3 scripts/wechat_mp_publish.py upload-article-image \
  --file ./assets/配图1-20260411-053407.png
```

上传封面图：

```bash
python3 scripts/wechat_mp_publish.py upload-thumb-image \
  --file ./assets/封面图-20260411-053407.png
```

发布草稿：

```bash
python3 scripts/wechat_mp_publish.py publish --media-id MEDIA_ID
```

查询发布状态：

```bash
python3 scripts/wechat_mp_publish.py get-publish-status --publish-id PUBLISH_ID
```

## 注意

- 默认建议先创建草稿，再人工确认后发布
- 正文图通常不走素材库，而是先上传成公众号正文可用 URL
- 封面图会上传为素材并返回 `thumb_media_id`
- 创建草稿前建议先看一眼 `--rendered-html-output` 导出的 HTML
- 只想先看排版效果时，用 `render-content` 最稳，不会触发任何公众号侧动作
