# Skill 分层策略

## 1. 背景

本项目会使用两类 skill：

- 开发辅助 skill：辅助开发者和 AI 编程助手理解项目、实现功能、遵守工程规范。
- 用户侧业务 skill：作为产品能力的一部分，帮助用户完成短剧创作流程。

两类 skill 的同步策略不同：

- 开发辅助 skill 不同步到 GitHub。
- 用户侧业务 skill 需要随着项目一起同步到 GitHub。

## 2. 目录约定

```text
.
├── .local-skills
│   └── ai-short-drama-dev
│       └── SKILL.md
└── skills
    └── short-drama-creator
        └── SKILL.md
```

## 3. 开发辅助 skill

开发辅助 skill 用于帮助 AI 编程助手在构建项目时保持上下文一致。

建议存放位置：

```text
.local-skills/
```

同步策略：

- 已加入 `.gitignore`。
- 不提交到 GitHub。
- 可以根据个人开发习惯自由调整。

当前初始 skill：

- `.local-skills/ai-short-drama-dev/SKILL.md`
- `.local-skills/frontend-nextjs-dev/SKILL.md`

适用场景：

- 实现第一期功能。
- 修改 FastAPI 后端。
- 修改 Next.js 前端。
- 按 `docs/technical/frontend-style-guide.md` 保持前端页面风格一致。
- 新增数据库表和 Alembic migration。
- 根据 PRD 和详细设计文档推进开发。

## 4. 用户侧业务 skill

用户侧业务 skill 是项目产品能力的一部分，用于沉淀短剧创作工作流。

建议存放位置：

```text
skills/
```

同步策略：

- 需要提交到 GitHub。
- 未来可以被后端服务读取，作为 AI 生成任务的工作流模板或提示词来源。
- 后续也可以按模块拆分为选题策划、故事大纲、人物设定、分集大纲、剧本生成、分镜拆解等 skill。

当前初始 skill：

- `skills/short-drama-creator/SKILL.md`

## 5. 后续扩展建议

开发辅助 skill 可以继续增加：

- `api-feature-dev`：后端功能开发规范。
- `db-migration-dev`：数据库迁移规范。

用户侧业务 skill 可以继续增加：

- `short-drama-topic-planner`：选题策划。
- `short-drama-story-outline`：整体故事大纲。
- `short-drama-character-designer`：人物设定和人物示意图提示词。
- `short-drama-episode-outliner`：分集大纲。
- `short-drama-script-writer`：单集剧本。
- `short-drama-storyboard-planner`：分镜拆解。
