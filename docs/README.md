# AI 短剧项目文档索引

## 文档层级

当前文档按“项目整体 -> 阶段 PRD -> 模块 PRD -> 按需前后端 Spec -> 技术规范”组织。

```text
docs
├── README.md
├── project
│   ├── background.md
│   └── roadmap.md
├── phase-1
│   ├── prd.md
│   ├── module-prds
│   │   └── README.md
│   ├── frontend-specs
│   │   └── README.md
│   └── backend-specs
│       └── README.md
└── technical
    ├── architecture.md
    ├── coding-standards.md
    ├── debugging.md
    ├── frontend-page-spec-template.md
    ├── frontend-style-guide.md
    ├── implementation-workflow.md
    ├── project-structure.md
    ├── skills-strategy.md
    └── spec-splitting-review.md
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

## 第一阶段模块 PRD

模块 PRD 用于在进入详细设计和实现前，单独描述某个功能的产品目标、范围、流程、数据对象和验收标准。

- [第一期模块 PRD 索引](./phase-1/module-prds/README.md)

## 第一阶段前端页面 Spec

前端页面 spec 用于在实现页面前明确页面目标、布局、交互、状态、API 依赖和验收标准。

- [第一期前端页面 Spec 说明](./phase-1/frontend-specs/README.md)

## 第一阶段后端接口 Spec

后端接口 spec 用于在实现 FastAPI 路由、Pydantic schema、service 业务规则和数据库迁移前明确接口合同。

- [第一期后端接口 Spec 说明](./phase-1/backend-specs/README.md)

## 后续文档建议

后续每个阶段可以沿用同样结构：

```text
docs
└── phase-n
    ├── prd.md
    ├── module-prds
    ├── backend-specs
    └── frontend-specs
```

新增或调整功能时，统一遵守 [功能实现流程规范](./technical/implementation-workflow.md)，按“PRD -> 按需后端接口 Spec -> 按需前端页面 Spec -> 代码实现 -> 验证”的顺序推进。

前端 spec 和后端 spec 按影响范围拆分，不要求每个功能都机械创建两份：影响 API、数据库、service 规则、模型调用或安全边界时更新后端 spec；影响页面布局、表单、交互、状态或前端校验时更新前端 spec。

## 技术文档

- [技术架构](./technical/architecture.md)
- [编码规范](./technical/coding-standards.md)
- [本地调试说明](./technical/debugging.md)
- [前端页面 Spec 模板](./technical/frontend-page-spec-template.md)
- [前端风格规范](./technical/frontend-style-guide.md)
- [功能实现流程规范](./technical/implementation-workflow.md)
- [项目结构约定](./technical/project-structure.md)
- [Skill 分层策略](./technical/skills-strategy.md)
- [前后端 Spec 拆分审查](./technical/spec-splitting-review.md)
