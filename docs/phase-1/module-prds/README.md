# 模块 PRD 索引

本目录包含第一期所有模块的详细 PRD（Layer 2）。文档按业务域分组，每个文档对应一个独立功能模块，定义该模块的字段、校验规则、状态机、用户故事和验收标准。

## 业务域与模块清单

| 业务域 | 模块 | 文档 | 状态 | 说明 |
|--------|------|------|------|------|
| 平台配置 | 模型 API 配置 | [model-api-settings.md](./platform/model-api-settings.md) | 已实现 | 文本/图片模型配置与连通性测试 |
| 项目管理 | 项目管理 | [project-management.md](./projects/project-management.md) | 已实现 | 项目创建、时长配置、列表管理 |
| 项目管理 | 项目工作台 | [project-workbench.md](./projects/project-workbench.md) | 已实现 | 三类入口、内容状态机、人工编辑 |
| 创作资产 | 创作资产库 | [creative-asset-library.md](./creative-assets/creative-asset-library.md) | 已实现 | 资产-项目架构总则 |
| 创作资产 | 世界观库 | [world-book-library.md](./creative-assets/world-book-library.md) | 已实现 | 世界观资产管理与项目加载 |
| 创作资产 | 角色卡库 | [character-card-library.md](./creative-assets/character-card-library.md) | 已实现 | 角色卡资产管理与项目加载 |
| 故事创作 | 选题策划生成 | [topic-planning.md](./story-creation/topic-planning.md) | 薄占位 | AI 生成选题方向 |
| 故事创作 | 整体故事大纲 | [story-outline.md](./story-creation/story-outline.md) | 已实现 | AI 生成故事骨架 |
| 故事创作 | 人物设定 | [character-design.md](./story-creation/character-design.md) | 薄占位 | AI 生成人物体系 |
| 故事创作 | 分集大纲 | [episode-outline.md](./story-creation/episode-outline.md) | 已实现 | AI 生成分集结构和单集故事正文 |
| 短剧制作 | 人物示意图 | [character-image.md](./production/character-image.md) | 薄占位 | AI 生成角色视觉参考 |
| 短剧制作 | 单集剧本 | [episode-script.md](./production/episode-script.md) | 薄占位 | AI 生成剧本与改写 |
| 内容管理 | 内容编辑 | [content-editing.md](./content-management/content-editing.md) | 薄占位 | 版本控制与编辑管理 |
| 内容管理 | Markdown 导出 | [markdown-export.md](./content-management/markdown-export.md) | 薄占位 | 项目内容导出 |

## 模块依赖关系

```text
模型 API 配置 ──────────────────────────────────┐
                                                 │ 所有 AI 生成任务的前置
项目管理 ────────────────────────────────────────┤
  │                                              │
  ├── 创作资产库 ── 世界观库 ──┐                │
  │                     角色卡库 ──┐             │
  │                               │             │
  └── 项目工作台（三类入口）──────┤             │
        │                        │             │
        ├── 选题策划生成 ◄────────┘◄────────────┘
        │     │
        │     └── 整体故事大纲
        │           │
        │           ├── 人物设定
        │           │     │
        │           │     └── 人物示意图
        │           │
        │           └── 分集大纲
        │                 │
        │                 └── 单集剧本
        │
        ├── 内容编辑与版本控制
        │
        └── Markdown 导出
```

## 数据对象索引

每个数据对象仅在一个模块文档中定义完整字段，其他文档仅引用。

| 数据对象 | 定义所在文档 |
|----------|------------|
| Project | [project-management.md](./projects/project-management.md) |
| TopicPlan | [topic-planning.md](./story-creation/topic-planning.md) |
| ModelApiConfig | [model-api-settings.md](./platform/model-api-settings.md) |
| ModelApiTestLog | [model-api-settings.md](./platform/model-api-settings.md) |
| WorldBook | [world-book-library.md](./creative-assets/world-book-library.md) |
| WorldEntry | [world-book-library.md](./creative-assets/world-book-library.md) |
| ProjectWorldSnapshot | [world-book-library.md](./creative-assets/world-book-library.md) |
| CharacterCard | [character-card-library.md](./creative-assets/character-card-library.md) |
| ProjectCharacterSnapshot | [character-card-library.md](./creative-assets/character-card-library.md) |
| ProjectArtifactStatus | [project-workbench.md](./projects/project-workbench.md) |
| ProjectStoryOutline | [project-workbench.md](./projects/project-workbench.md) |
| Character | [project-workbench.md](./projects/project-workbench.md) |
| CharacterImage | [project-workbench.md](./projects/project-workbench.md) |
| ProjectEpisodeOutline | [project-workbench.md](./projects/project-workbench.md) |
| ProjectEpisodeContent | [project-workbench.md](./projects/project-workbench.md) |
| ProjectEpisodeScript | [project-workbench.md](./projects/project-workbench.md) |
| ProjectStoryboardShot | [project-workbench.md](./projects/project-workbench.md) |
| ProjectCopywriting | [project-workbench.md](./projects/project-workbench.md) |
| GenerationVersion | [project-workbench.md](./projects/project-workbench.md) |

## 编写约定

每个 Layer 2 模块文档应包含以下章节：

1. **功能定位** — 一句话说明模块解决什么问题。
2. **背景/用户场景**（可选）— 适用时提供用户场景。
3. **功能范围** — 第一期包括什么、不包括什么。
4. **字段设计/数据对象** — 模块涉及的数据对象完整字段定义。
5. **校验规则/状态规则** — 字段校验和状态流转。
6. **交互要求** — 用户可执行的操作（不涉及具体页面布局）。
7. **用户故事** — 该模块相关的用户故事编号和内容。
8. **验收标准** — 可测试的验收条目。
9. **实现决策**（可选）— 已做出的技术或产品决策。
10. **后续扩展**（可选）— 未来版本可能增加的能力。
11. **关联文档** — 指向相关的 Layer 1（prd.md）、后端接口 spec（backend-specs/）和前端页面 spec（frontend-specs/）文档。
