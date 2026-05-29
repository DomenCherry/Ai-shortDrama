# AI 短剧项目文档索引

## 文档层级

当前文档按“项目整体 -> 阶段 PRD -> 功能详细设计”组织。

```text
docs
├── README.md
├── project
│   ├── background.md
│   └── roadmap.md
└── phase-1
    ├── prd.md
    └── features
        ├── model-api-settings.md
        └── project-creation.md
```

## 项目级文档

项目级文档描述整个 AI 短剧制作系统的长期方向、整体目标和阶段拆分。

- [项目背景](./project/background.md)
- [项目分期规划](./project/roadmap.md)

## 第一阶段文档

第一阶段文档描述第一期要完成的产品范围和功能需求。

- [第一期 PRD](./phase-1/prd.md)

## 第一阶段功能详细设计

功能详细设计文档用于展开第一期 PRD 中的单个功能，方便后续直接进入实现。

- [项目创建与时长配置](./phase-1/features/project-creation.md)
- [模型 API 配置与连通性测试](./phase-1/features/model-api-settings.md)

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
- [本地调试说明](./technical/debugging.md)
- [Skill 分层策略](./technical/skills-strategy.md)
