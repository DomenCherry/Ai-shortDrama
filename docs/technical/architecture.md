# 技术架构 v0.1

## 1. 架构目标

第一期技术框架优先支持单用户、本地开发和快速迭代，同时为后续产品化预留扩展空间。

核心目标：

- 前端可以承载项目工作台和配置页面。
- 后端可以统一管理项目数据、模型 API 配置和生成任务入口。
- 数据库使用 PostgreSQL，避免后续进入素材、发布、账号和团队协作阶段时再迁移主数据库。
- 文本模型和图片模型先按 OpenAI-compatible API 形态接入，后续再抽象多供应商适配层。

## 2. 技术选型

- 前端：Next.js + TypeScript。
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

后续预留但暂不实现：

- `generation`：文本生成、图片生成和 AI 任务记录。
- `assets`：人物示意图和本地素材管理。
- `workspace`：项目工作区目录和导出文件写入。

前端继续保持 App Router 和集中 API service 层。页面复杂度上升后，再新增 `components`、`features`、`types` 等目录。

## 5. 一期核心模块

- Settings：模型 API 配置与连通性测试。
- Projects：项目创建与时长配置。
- Generation：后续承载选题、故事大纲、人物、分集和剧本生成。

## 6. 数据策略

第一期使用 PostgreSQL 保存：

- 模型 API 配置。
- 模型 API 测试记录。
- 项目基础信息。

API Key 当前仅做接口返回脱敏，后续需要在产品化前增加系统级加密存储。

当前本地数据库连接：

```text
postgresql+psycopg://ai_short_drama:ai_short_drama@127.0.0.1:5432/ai_short_drama
```

## 7. 接口边界

当前优先实现：

- `GET /health`
- `GET /api/model-configs`
- `POST /api/model-configs`
- `POST /api/model-configs/{config_id}/test`
- `GET /api/projects`
- `POST /api/projects`

## 8. 数据迁移

数据库 schema 通过 Alembic 管理：

```bash
npm run db:migrate
```

当前初始迁移文件：

```text
apps/api/alembic/versions/0001_initial_schema.py
```
