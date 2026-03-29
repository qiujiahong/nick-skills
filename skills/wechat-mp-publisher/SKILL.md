---
name: wechat-mp-publisher
description: 自动发布微信公众号文章。支持通过微信公众号接口创建草稿，并可选择提交发布。凭证从环境变量注入，适用于把 Markdown/HTML 内容发到公众号。
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

需要先配置公众号接口凭证：

- `WECHAT_MP_APP_ID`
- `WECHAT_MP_APP_SECRET`

可选：

- `WECHAT_MP_THUMB_MEDIA_ID` — 默认封面 media_id
- `WECHAT_MP_AUTHOR` — 默认作者名
- `WECHAT_MP_BASE_URL` — 默认 `https://api.weixin.qq.com/cgi-bin`

## 工作流程

1. 整理文章内容：标题、作者、摘要、正文
2. 如果正文是 Markdown，可先转成适合公众号的 HTML
3. 调用脚本获取 access token
4. 创建草稿
5. 只有在用户明确要求“直接发布”时，才调用发布接口
6. 返回草稿 ID / publish_id / 状态信息

## 安全规则

- 默认只创建草稿，不直接发布
- 真正对外发布前，最好给用户看一眼标题、摘要和封面
- 不要擅自替用户发文

## 使用方式

### 创建草稿

```bash
python3 scripts/wechat_mp_publish.py create-draft \
  --title "用 OpenClaw 自动化技能开发" \
  --author "Nick" \
  --digest "这是一篇介绍 OpenClaw skills 的文章" \
  --content-file article.html \
  --thumb-media-id "$WECHAT_MP_THUMB_MEDIA_ID"
```

### 直接从 Markdown 创建草稿

```bash
python3 scripts/wechat_mp_publish.py create-draft \
  --title "用 OpenClaw 自动化技能开发" \
  --content-file article.md \
  --content-format markdown
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
- `publish`：提交发布草稿
- `get-publish-status`：查询发布进度
- Markdown 支持基础转换，但复杂公众号排版建议先人工预览
