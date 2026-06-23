# 技术架构 v0.1

## 1. 架构目标

第一期技术框架优先支持单用户、本地开发和快速迭代，同时为后续产品化预留扩展空间。

核心目标：

- 前端可以承载项目工作台和配置页面。
- 后端可以统一管理项目数据、模型 API 配置和生成任务入口。
- 数据库使用 PostgreSQL，避免后续进入素材、发布、账号和团队协作阶段时再迁移主数据库。
- 文本模型和图片模型先按 OpenAI-compatible API 形态接入，后续再抽象多供应商适配层。

## 2. 技术选型

- 前端：Next.js + TypeScript + Tailwind CSS + shadcn/ui。
- 后端：Python 3.11 + FastAPI + PostgreSQL。
- 数据访问：SQLAlchemy。
- 数据迁移：Alembic。
- API 调用：HTTP JSON。
- 本地数据库：Docker Compose 启动 PostgreSQL。

## 3. 应用结构

```text
apps
├── web
│   ├── app
│   ├── components
│   └── lib
└── api
    └── app
        ├── api
        ├── core
        ├── models
        └── services
```

仓库级配套结构：

```text
.
├── docs
├── rules
├── skills
└── workspace
```

- `rules` 保存用户侧短剧创作规则。
- `skills` 保存用户侧业务 skill。
- `workspace` 保存本地运行产物约定，具体项目产物默认不提交 GitHub。

更详细的结构说明见 [项目结构约定](./project-structure.md)。

## 4. 模块边界

后端继续保持 `api / core / models / services` 分层。

Projects 后端已做行为不变的结构性拆分：

- `api/projects.py` 保留为 `/api/projects` 路由聚合器。
- `api/project_routes/` 按项目基础、资产、故事文本和短剧制作拆分 route。
- `services/projects.py` 保留为兼容 facade。
- `services/project/` 按项目基础、资产、故事文本、短剧制作和生成公共能力拆分业务逻辑。

该拆分不改变 HTTP 路径、请求体、响应体、数据库 schema 或前端 API client。

后续预留但暂不实现：

- `generation`：文本生成、图片生成和 AI 任务记录。
- `assets`：人物示意图和本地素材管理。
- `workspace`：项目工作区目录和导出文件写入。

前端继续保持 App Router、集中 API service 层和 shadcn/ui 基础组件层。`components/ui` 用于维护跨页面基础 UI，页面或业务模块新增基础控件前必须先检查 [前端 UI 组件库规范](./ui-component-library.md)。

## 5. 一期核心模块

- Settings：模型 API 配置与连通性测试。
- Skills：用户侧业务 Skill 展示与全局启用开关。
- Projects：项目创建与时长配置。
- Generation：后续承载选题、故事大纲、人物、分集和剧本生成。

## 6. 数据策略

第一期使用 PostgreSQL 保存：

- 模型 API 配置。
- 模型 API 测试记录。
- 用户侧业务 Skill 全局启用设置。
- 项目基础信息。

API Key 当前仅做接口返回脱敏，后续需要在产品化前增加系统级加密存储。

当前本地数据库连接：

```text
postgresql+psycopg://ai_short_drama:ai_short_drama@127.0.0.1:5432/ai_short_drama
```

## 7. 接口边界

当前接口按业务模块分组管理。项目工作台相关接口必须遵守 [项目工作台资产快照后端 Spec](../phase-1/backend-specs/project-workbench-assets.md)。

基础接口：

- `GET /health`

模型配置接口：

- `GET /api/model-configs`
- `POST /api/model-configs`
- `POST /api/model-configs/{config_id}/test`

用户侧 Skill 管理接口：

- `GET /api/skills`
- `PATCH /api/skills/{skill_name}`

项目接口：

- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `PUT /api/projects/{project_id}`

项目资产快照接口：

- `GET /api/projects/{project_id}/world-snapshots`
- `POST /api/projects/{project_id}/world-snapshots`
- `PUT /api/projects/{project_id}/world-snapshots/{snapshot_id}`
- `DELETE /api/projects/{project_id}/world-snapshots/{snapshot_id}`
- `GET /api/projects/{project_id}/character-snapshots`
- `POST /api/projects/{project_id}/character-snapshots`
- `PUT /api/projects/{project_id}/character-snapshots/{snapshot_id}`
- `DELETE /api/projects/{project_id}/character-snapshots/{snapshot_id}`

项目资产快照业务边界：

- 每个项目最多一个世界观快照。
- 每个项目可以有多个角色快照，但同一角色卡不能重复加载到同一项目。
- 项目快照微调不回写资产库原始内容。
- 加载、替换、更新或删除项目快照后，下游已有创作内容应标记为 `needs_review`。

## 8. 数据迁移

数据库 schema 通过 Alembic 管理：

```bash
npm run db:migrate
```

当前初始迁移文件：

```text
apps/api/alembic/versions/0001_initial_schema.py
```
