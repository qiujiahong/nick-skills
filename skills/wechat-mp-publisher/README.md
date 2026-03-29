# wechat-mp-publisher

微信公众号自动发文 skill。

## 当前能力

- 获取公众号 `access_token`
- 创建草稿（draft/add）
- 提交发布（freepublish/submit）
- 查询发布状态（freepublish/get）
- 支持 HTML / Markdown 正文输入
- 凭证通过环境变量注入

## 环境变量

```bash
export WECHAT_MP_APP_ID="wx123..."
export WECHAT_MP_APP_SECRET="abcdef..."
export WECHAT_MP_AUTHOR="Nick"
export WECHAT_MP_THUMB_MEDIA_ID="MEDIA_ID"
```

## 用法

创建草稿：

```bash
python3 scripts/wechat_mp_publish.py create-draft \
  --title "我的第一篇自动发文测试" \
  --content-file article.md \
  --content-format markdown
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
- 封面图 `thumb_media_id` 需要你提前在公众号素材库里准备好
- 如果需要，我后续还能再补“上传封面图素材”“自动摘要”“定时发布”等能力
