# 项目结构约定

## 1. 目标

本项目采用“应用代码、创作规则、运行产物分离”的结构。

目标是让 AI 短剧创作工具在早期保持简单，同时为后续故事生成、人物示意图、素材管理、导出和视频制作预留清晰边界。

## 2. 仓库结构

```text
.
├── apps
│   ├── api
│   └── web
├── docs
├── rules
├── skills
├── workspace
└── .local-skills
```

目录说明：

- `apps/api`：FastAPI 后端。
- `apps/web`：Next.js 前端。
- `docs`：产品、阶段、功能和技术文档。
- `rules`：用户侧短剧创作规则，需要同步到 GitHub。
- `skills`：用户侧业务 skill，需要同步到 GitHub。
- `workspace`：本地项目产物目录，具体运行产物不提交 GitHub。
- `.local-skills`：本地开发辅助 skill，不提交 GitHub。

## 3. 工作区策略

`workspace/projects/` 用于保存具体短剧项目的本地产物。

约定结构：

```text
workspace/projects/<project-id>
├── metadata.json
├── exports
├── assets
│   └── characters
├── generations
└── scripts
```

Git 策略：

- 提交 `workspace/README.md` 和 `workspace/projects/.gitkeep`。
- 忽略 `workspace/projects/*` 下的具体项目产物。
- 不把人物示意图、导出文件、生成历史和素材文件提交到 GitHub。

## 4. Rules 与 Skills 分工

用户侧创作能力分为两层：

- `skills/short-drama-creator/SKILL.md`：定义触发场景、核心流程和规则路由。
- `rules/*.md`：定义每个创作模块的产出结构、质量要求和检查点。

当前规则包括：

- 选题策划。
- 整体故事大纲。
- 人物设定。
- 人物示意图。
- 分集大纲。
- 单集剧本。

后续新增创作模块时，优先补充独立 rule，再更新 skill 路由。

## 5. 后端模块边界

当前后端保持：

```text
apps/api/app
├── api
├── core
├── models
└── services
```

约定：

- `api`：HTTP 路由和请求响应边界。
- `core`：配置、数据库连接和底层基础设施。
- `models`：SQLAlchemy 模型和 Pydantic schema。
- `services`：业务逻辑。

后续预留服务模块：

- `generation`：文本生成、图片生成和 AI 任务记录。
- `assets`：人物示意图、本地素材和资源索引。
- `workspace`：项目工作区目录创建、路径解析和导出文件写入。

本次结构调整不新增数据库表，不新增 Alembic migration。

## 6. 前端模块边界

当前前端保持：

```text
apps/web
├── app
└── lib
```

约定：

- `app`：Next.js App Router 页面。
- `lib/api.ts`：前端 API service 层，页面不直接散落复杂 fetch 逻辑。

后续当页面复杂度上升后，再新增：

```text
apps/web
├── components
├── features
└── types
```

使用规则：

- `components`：跨页面复用的通用 UI。
- `features`：按业务模块组织的组件和状态逻辑。
- `types`：前端共享类型。

新增目录应以实际重复和复杂度为依据，不提前抽象。

## 7. 前端页面 Spec

新增页面、重构页面、复杂交互页面或 AI 生成工作台页面，在实现前应先创建或更新页面 spec。

页面 spec 存放位置：

```text
docs/phase-1/frontend-specs/<page-name>.md
```

页面 spec 模板：

```text
docs/technical/frontend-page-spec-template.md
```

页面 spec 用于描述：

- 页面目标。
- 用户流程。
- 信息架构。
- 布局结构。
- 字段与控件。
- 交互状态。
- API 依赖。
- 错误提示。
- 响应式要求。
- 验收标准。

页面 spec 只描述前端行为和验收，不替代 PRD、功能详细设计或后端接口设计。
