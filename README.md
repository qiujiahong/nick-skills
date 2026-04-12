# nick-skills

OpenClaw / Codex 可复用技能集合，包含图像生成、视频生成、语音合成、语音导演、教学视频生成、技术博客生产链，以及 OpenClaw 团队配置类 skill。

## 目录结构

```text
skills/
  image-gen/
  video-gen/
  teaching-video-maker/
  voice-tts/
  voice-director/
  ai-topic-research/
  tavily-search/
  tech-blog-writer/
  wechat-mp-publisher/
  openclaw-team-setup/
  openclaw-codex-account-switch/
  agent-provisioning/
  fin-ai-daily-brief/
dist/
```

`skills/` 下是可直接使用的 skill 源码目录，`dist/` 下是已打包产物。

## Skill 列表

| Skill | 描述 |
|-------|------|
| [image-gen](skills/image-gen/) | AI 图像生成与编辑，支持文生图、图+文生图、风格转换，多比例与标准 / 2K / 4K 分辨率 |
| [video-gen](skills/video-gen/) | AI 视频生成与编辑，基于火山引擎 Doubao Seedance，支持文生视频、图生视频、有声视频 |
| [teaching-video-maker](skills/teaching-video-maker/) | 生成有声音的教学视频；调用 `remotion` skill 编排画面，并使用本地 `microsoft/VibeVoice-1.5B` 或可配置 VibeVoice 服务生成拟人旁白，支持授权声音克隆 |
| [voice-tts](skills/voice-tts/) | 火山引擎语音合成，支持声音复刻音色、语速 / 语调 / 情感控制 |
| [voice-director](skills/voice-director/) | 用 LLM 为台词自动标注情感、语速、语调，再交给 `voice-tts` 合成 |
| [ai-topic-research](skills/ai-topic-research/) | 面向 AI 技术主题与技术社区热点的联网研究；既能研究单个主题，也能从社区热点里只推荐 1 个适合写博客的主题 |
| [tavily-search](skills/tavily-search/) | Tavily 联网搜索封装，供研究类 skill 收集资料 |
| [tech-blog-writer](skills/tech-blog-writer/) | 技术博客写作中枢；根据“已选主题 + 素材资料 + 写作建议”在 `tech-blog-writer/YYYYMMDD/` 下生成博客文件夹，包含 `blog.md`、`image-requirements.md` 和 `assets/` |
| [wechat-mp-publisher](skills/wechat-mp-publisher/) | 将 Markdown / HTML 渲染成公众号风格 HTML，上传封面和正文图片，创建公众号草稿，并在确认后发布 |
| [openclaw-team-setup](skills/openclaw-team-setup/) | 标准化配置或修复 OpenClaw 多智能体团队，覆盖 agent 拓扑、ACP、Feishu 路由与验证 |
| [openclaw-codex-account-switch](skills/openclaw-codex-account-switch/) | 在 OpenClaw 环境中切换或重配 OpenAI Codex 账号，并完成登录与连通性验收 |
| [agent-provisioning](skills/agent-provisioning/) | 创建或修复单个 OpenClaw / ACP agent，并绑定指定的 Feishu 机器人与 routing binding |
| [fin-ai-daily-brief](skills/fin-ai-daily-brief/) | 搜索 20 条金融 + AI 资讯，筛选出最有价值的 10 条，生成 HTML 资讯页并通过 SMTP 邮件发送 |

## 安装方式

按需将目标 skill 目录复制或链接到你的 OpenClaw skills 目录中即可。

```bash
cp -R skills/<skill-name> /path/to/openclaw/skills/
```

如果你的环境支持打包分发，也可以直接使用 `dist/` 下的产物。

## 技术博客流水线

完整博客生产默认串联这些 skill：

1. `ai-topic-research`：用 `discover` 模式先选题，输入种子方向和最近 10 天已写主题，输出“选择主题 / 支撑链接 / 写作建议”
2. 围绕已选主题补素材：再做一轮搜索，把关键事实、关键观点、可用案例和对比角度整理成笔记
3. `tech-blog-writer`：生成 `tech-blog-writer/YYYYMMDD/<topic-slug>/` 目录，固定包含 `blog.md`、`image-requirements.md` 和 `assets/`
4. `image-gen`：根据 `image-requirements.md` 逐张生成封面图和正文图，图片文件写入 `assets/`
5. `wechat-mp-publisher`：先 `render-content` 本地渲染，再 `create-draft` 创建公众号草稿，用户确认后才 `publish`

博客产物目录约定：

```text
tech-blog-writer/YYYYMMDD/<topic-slug>/
  blog.md
  image-requirements.md
  assets/
```

流程规则：

- 不要直接拿 `discover` 结果开写；必须先补一轮真正可写作的素材资料
- `blog.md` 必须预留正文图片占位符，例如 `[配图1](./assets/配图1-YYYYMMDD-HHMMSS.png)`
- `image-requirements.md` 开头必须先写“整体要求”，默认风格预设为 `清新手绘风`
- `image-requirements.md` 必须额外包含 1 张封面图，正文图片编号要和 `blog.md` 占位符一一对应
- 至少 1 张正文图要做成可截图收藏的对照图、流程图或行动指南图
- 同一篇文章的图片文件名尽量复用同一个时间标签，便于发布时去重和追踪
- 生成图片时一次最多并发 `2` 个任务；遇到 `429`、upstream overloaded、长时间无返回或文件未落盘时，记录失败图片并单张重试
- 涉及 `最流行`、`最热门`、`Top N`、`最常用`、`最值得装`、`爆火` 这类主题时，必须先补外部社区证据，不能把本地仓库内容当成热门度依据
- 面向中文 / 国内读者时，不要默认把 Google、Gmail、Google Workspace、YouTube、X/Twitter 等作为主路径；强依赖海外服务时要写清国内使用前提或替代路径
- 发布公众号前必须能生成本地渲染 HTML；默认只创建草稿，不擅自直接发布

## 环境变量

不同 skill 使用不同环境变量：

### image-gen

```bash
export IMAGE_GEN_API_KEY="your-api-key"
export IMAGE_GEN_BASE_URL="https://api.apiyi.com"
export IMAGE_GEN_MODEL="gemini-3.1-flash-image-preview"
export IMAGE_GEN_ASPECT_RATIO="16:9"
export IMAGE_GEN_IMAGE_SIZE="2K"
```

### video-gen

```bash
export VIDEO_GEN_API_KEY="your-api-key"
export VIDEO_GEN_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
```

### teaching-video-maker

第一次使用前安装 Remotion skill：

```bash
npx skills add https://github.com/google-labs-code/stitch-skills --skill remotion
```

默认使用本地 VibeVoice：

```bash
export TEACHING_VIDEO_TTS_ENGINE="vibevoice"
export VIBEVOICE_MODEL="microsoft/VibeVoice-1.5B"
export VIBEVOICE_ENDPOINT="http://127.0.0.1:7860"
export VIBEVOICE_SPEAKER_ID="Bowen"
export VIBEVOICE_SEED="1227"
# 可选：授权声音克隆参考音频
export VIBEVOICE_VOICE_REF="/absolute/path/to/authorized-reference.wav"
```

如果本地没有可用的 VibeVoice endpoint 或命令，先运行：

```bash
skills/teaching-video-maker/scripts/ensure_vibevoice.sh
source "$HOME/.cache/nick-skills/vibevoice/env.sh"
```

最终视频输出目录会同时包含可直接发视频号的总结文案：

```text
teaching-video/YYYYMMDD/<topic-slug>/output/<topic-slug>-summary.md
```

### voice-tts

```bash
export NICK_SKILLS_ENV_VOICE_TTS_API_KEY="your-api-key"
export NICK_SKILLS_ENV_VOICE_TTS_VOICE_TYPE="S_xxxxxxxx"
export NICK_SKILLS_ENV_VOICE_TTS_CLUSTER="volcano_icl"
```

### voice-director

```bash
export NICK_SKILLS_ENV_DIRECTOR_API_KEY="your-api-key"
export NICK_SKILLS_ENV_DIRECTOR_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
export NICK_SKILLS_ENV_DIRECTOR_MODEL="doubao-1.5-pro-256k"
```

### ai-topic-research

```bash
export TAVILY_API_KEYS="tvly-key-1,tvly-key-2"
export TAVILY_SEARCH_BASE_URL="https://api.tavily.com"
```

### wechat-mp-publisher

```bash
export WECHAT_MP_APP_ID="your-app-id"
export WECHAT_MP_APP_SECRET="your-app-secret"
```

## 使用建议

- 图像生成直接看 [image-gen](skills/image-gen/)。
- 视频生成直接看 [video-gen](skills/video-gen/)。
- 需要根据主题生成有声音的教学视频时，使用 [teaching-video-maker](skills/teaching-video-maker/)；输入“视频主题”必填，“内容要求 / 风格要求 / 时间要求”可选，默认 3 分钟、简洁科技风、本地 VibeVoice 旁白。
- 需要更有表现力的配音时，先用 [voice-director](skills/voice-director/) 标注，再用 [voice-tts](skills/voice-tts/) 合成。
- 需要围绕 `MCP`、`RAG`、`AI Coding Agent`、`Responses API` 这类主题快速做第一轮资料研究时，使用 [ai-topic-research](skills/ai-topic-research/)。
- 需要完整生产技术博客时，按 `ai-topic-research -> 补素材 -> tech-blog-writer -> image-gen -> wechat-mp-publisher` 的顺序执行。
- 需要把“选题 + 素材资料 + 写作建议”整理成博客文件夹，并输出正文与配图要求时，使用 [tech-blog-writer](skills/tech-blog-writer/)，默认产物放在 `tech-blog-writer/YYYYMMDD/`。
- 需要把博客渲染成公众号 HTML、上传封面和正文图片、创建草稿或发布时，使用 [wechat-mp-publisher](skills/wechat-mp-publisher/)。
- 需要搭建或修复 OpenClaw 项目团队时，使用 [openclaw-team-setup](skills/openclaw-team-setup/)。
- 需要切换 OpenClaw 上的 Codex OAuth 账号时，使用 [openclaw-codex-account-switch](skills/openclaw-codex-account-switch/)。
- 需要新建单个 agent、绑定 Feishu 机器人并校验状态时，使用 [agent-provisioning](skills/agent-provisioning/)。
- 需要生成金融 AI 日报、邮件订阅资讯页时，使用 [fin-ai-daily-brief](skills/fin-ai-daily-brief/)。
