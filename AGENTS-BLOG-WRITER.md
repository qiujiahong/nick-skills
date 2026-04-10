# AGENTS-BLOG-WRITER.md

这个文件定义“博客写作 Agent”未来的标准调用流程。

目标：

- 先选题
- 再生成博客目录
- 再生成整套配图
- 让不同 agent 后续都按同一套路径和节奏执行

## 目录约定

所有博客产物默认放在：

```text
tech-blog-writer/YYYYMMDD/<topic-slug>/
```

目录内固定包含：

```text
tech-blog-writer/YYYYMMDD/<topic-slug>/
  blog.md
  image-requirements.md
  assets/
```

说明：

- `blog.md`：博客正文
- `image-requirements.md`：配图要求
- `assets/`：实际图片文件

## 标准流程

### 1. 选题

先调用 `ai-topic-research` 的 `discover` 模式。

输入通常包含：

- 种子方向，例如 `AI编程`
- 最近 10 天已经写过的主题

输出只保留三块：

- 选择主题
- 支撑链接
- 写作建议

### 2. 写博客

再调用 `tech-blog-writer`。

输入：

- 选择主题
- 支撑链接
- 写作建议

输出：

- `blog.md`
- `image-requirements.md`

要求：

- `blog.md` 里必须预留图片占位符，例如 `[配图1](./assets/配图1.png)`
- `image-requirements.md` 开头必须先写“整体要求”
- `image-requirements.md` 里的图片编号，必须和 `blog.md` 中占位符一一对应

### 3. 生成配图

最后调用 `image-gen`，逐张生成 `assets/` 里的图片文件。

输入来源：

- `image-requirements.md`

输出目标：

- `assets/配图1.png`
- `assets/配图2.png`
- `assets/配图3.png`
- ...

## 图片生成并发规则

非常重要：

- 一次最多只允许 `2` 个并发图片生成任务
- 不允许一次性把 3 张或 4 张图同时发给上游

推荐执行方式：

1. 先启动 2 张
2. 任意 1 张完成后，再补下一张
3. 始终保持并发数 `<= 2`

这样做的原因：

- 上游更容易限流
- 同时跑太多张时更容易出现 `429`
- 串行补位更容易排查失败图片

## 图片生成失败处理

如果出现以下情况：

- `429`
- upstream overloaded
- 长时间无返回
- 输出文件未落盘

处理规则：

1. 不要继续增加新的并发任务
2. 记录失败的是哪一张图
3. 对失败图片单独重试
4. 重试时优先降低压力：
   - 保持单张重试
   - 必要时降低 `image-size`
   - 必要时简化 prompt

建议：

- 某张图连续失败时，先让其他已成功的图保留，不要整批重跑
- 对比图、结构图这类复杂信息图，更容易触发慢请求，应该优先单独重试

## Prompt 组织规则

所有图片 prompt 都要先继承 `image-requirements.md` 里的“整体要求”。

也就是每张图都应该保持：

- 同一套主色系
- 同类构图风格
- 同类信息图语言
- 同类字体与标注感觉

再叠加每张图自己的：

- 用途
- 内容
- 比例
- 放置位置

## 产出校验

在流程结束前，必须检查：

- `blog.md` 存在
- `image-requirements.md` 存在
- `assets/` 存在
- `blog.md` 中所有 `[配图N](./assets/配图N.png)` 都有对应文件
- `image-requirements.md` 中列出的图片数量，和实际生成数量一致

## 当前推荐顺序

未来 agent 调用时，默认按这个顺序：

1. `ai-topic-research`
2. `tech-blog-writer`
3. `image-gen`

不要跳过中间产物。

原因：

- 选题卡片是写作输入
- 写作结果决定配图需求
- 配图要求再决定图片 prompt

这是一个严格串联流程，不是三个互相独立的步骤。
