# AI 短剧项目文档索引

## 文档层级

当前文档按“项目整体 -> 阶段 PRD -> 功能详细设计”组织。

```text
docs
├── README.md
├── project
│   ├── background.md
│   └── roadmap.md
├── phase-1
│   ├── prd.md
│   ├── prds
│   │   └── character-card-library-prd.md
│   ├── frontend-specs
│   │   └── README.md
│   └── features
│       ├── character-card-library.md
│       ├── creative-asset-library.md
│       ├── model-api-settings.md
│       ├── project-creation.md
│       └── world-book-library.md
└── technical
    ├── architecture.md
    ├── coding-standards.md
    ├── debugging.md
    ├── frontend-page-spec-template.md
    ├── frontend-style-guide.md
    ├── project-structure.md
    └── skills-strategy.md
```

仓库级配套目录：

```text
.
├── rules
├── skills
└── workspace
```

- `rules`：用户侧短剧创作规则。
- `skills`：用户侧业务 skill。
- `workspace`：本地项目产物工作区，具体运行产物默认不提交 GitHub。

## 项目级文档

项目级文档描述整个 AI 短剧制作系统的长期方向、整体目标和阶段拆分。

- [项目背景](./project/background.md)
- [项目分期规划](./project/roadmap.md)

## 第一阶段文档

第一阶段文档描述第一期要完成的产品范围和功能需求。

- [第一期 PRD](./phase-1/prd.md)

## 第一阶段功能 PRD

功能 PRD 用于在进入详细设计和实现前，单独描述某个功能的产品目标、范围、流程、数据对象和验收标准。

- [角色卡库 PRD](./phase-1/prds/character-card-library-prd.md)

## 第一阶段功能详细设计

功能详细设计文档用于展开第一期 PRD 中的单个功能，方便后续直接进入实现。

- [创作资产库](./phase-1/features/creative-asset-library.md)
- [世界观库](./phase-1/features/world-book-library.md)
- [角色卡库](./phase-1/features/character-card-library.md)
- [项目创建与时长配置](./phase-1/features/project-creation.md)
- [模型 API 配置与连通性测试](./phase-1/features/model-api-settings.md)

## 第一阶段前端页面 Spec

前端页面 spec 用于在实现页面前明确页面目标、布局、交互、状态、API 依赖和验收标准。

- [第一期前端页面 Spec 说明](./phase-1/frontend-specs/README.md)

## 后续文档建议

后续每个阶段可以沿用同样结构：

```text
docs
└── phase-n
    ├── prd.md
    └── features
        ├── feature-a.md
        └── feature-b.md
```

如果某个功能进入技术实现阶段，可以继续在对应阶段下增加：

```text
docs
└── phase-n
    ├── prd.md
    ├── features
    └── technical-design
```

## 技术文档

- [技术架构](./technical/architecture.md)
- [编码规范](./technical/coding-standards.md)
- [本地调试说明](./technical/debugging.md)
- [前端页面 Spec 模板](./technical/frontend-page-spec-template.md)
- [前端风格规范](./technical/frontend-style-guide.md)
- [项目结构约定](./technical/project-structure.md)
- [Skill 分层策略](./technical/skills-strategy.md)
