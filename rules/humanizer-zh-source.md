# Humanizer-zh 来源说明

- 来源仓库：[op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)
- 引入用途：作为单集故事正文 AI 创作、续写、润色的提示规则来源，用于减少中文文本中的常见 AI 腔。
- 许可：MIT License（以来源仓库许可为准）。
- 项目运行时安装路径：`runtime-skills/humanizer-zh`。
- 本项目用法：不在运行时调用 Codex / Claude skill 命令；后端读取项目运行时目录中的 `SKILL.md`，再叠加 `rules/episode-content-humanizer-rule.md` 的短剧正文适配规则，与正文生成请求在同一次文本模型调用中融合。
- 适用范围：仅限故事文本 → 单集故事正文的 `create` / `continue` / `polish` 候选稿生成。
- 不适用范围：整体大纲、分集大纲、摘要、质检、剧本、分镜、文案等结构化或非正文功能。
