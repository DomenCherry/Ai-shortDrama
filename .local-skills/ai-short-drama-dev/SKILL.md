---
name: ai-short-drama-dev
description: 在本地开发 AI 短剧项目时使用，包括阅读项目文档、实现阶段功能、更新 FastAPI 接口、Next.js 页面、PostgreSQL 模型、Alembic 迁移，并保持实现与 PRD 和详细设计文档一致。此 skill 仅用于本地开发，不应提交到 GitHub。
---

# AI 短剧项目开发辅助

## 用途

当需要实现、重构或维护本项目时使用此 skill。

这是一个本地开发专用 skill，不应同步到 GitHub。

## 项目上下文

- 产品文档位于 `docs/`。
- 项目级文档位于 `docs/project/`。
- 第一期 PRD 位于 `docs/phase-1/prd.md`。
- 模块 PRD 位于 `docs/phase-1/module-prds/`。
- 后端接口 spec 位于 `docs/phase-1/backend-specs/`。
- 前端页面 spec 位于 `docs/phase-1/frontend-specs/`。
- 技术文档位于 `docs/technical/`。
- 功能实现流程规范位于 `docs/technical/implementation-workflow.md`。
- 编码规范位于 `docs/technical/coding-standards.md`。
- 前端风格规范位于 `docs/technical/frontend-style-guide.md`。
- 后端代码位于 `apps/api`。
- 前端代码位于 `apps/web`。
- 用户侧产品 skill 位于 `skills/`。

## 开发流程

1. 修改代码前先阅读 `docs/technical/implementation-workflow.md`，确认本次需求属于模块 PRD、后端接口 spec、前端页面 spec、代码实现或技术规范中的哪个层级。
2. 新增功能或复杂交互必须先补齐模块 PRD，并按影响范围更新后端接口 spec 或前端页面 spec，再进入代码实现。
3. 修改代码前先阅读相关模块 PRD、后端接口 spec 和前端页面 spec。
4. 保持实现范围聚焦在当前请求的功能内。
5. 当行为、命令、数据结构或架构发生变化时，同步更新文档。
6. 主数据库使用 PostgreSQL。
7. 数据库表使用 SQLAlchemy 模型定义。
8. 数据库结构变更使用 Alembic migration。
9. FastAPI 路由模块放在 `apps/api/app/api`。
10. 业务逻辑服务模块放在 `apps/api/app/services`。
11. Next.js App Router 页面放在 `apps/web/app`。
12. 修改代码时遵守 `docs/technical/coding-standards.md`，关键业务规则、状态流转、安全边界和生成上下文规则必须有中文注释。
13. 修改前端页面时遵守 `docs/technical/frontend-style-guide.md`。
14. 修改完成后运行与改动范围匹配的检查，并自检注释是否解释了非显然逻辑。

## 本地 skill 路由

根据任务类型优先使用对应的本地开发 skill：

- 遇到 bug、接口异常、构建失败、集成问题：使用 `systematic-debugging`。
- 新增功能、修复缺陷、需要验证行为：使用 `tdd-and-verification`。
- 修改 `apps/web`、Next.js 页面、React 组件、前端交互、页面风格：使用 `frontend-nextjs-dev`。
- 修改 `apps/api`、FastAPI 路由、Pydantic schema、服务层：使用 `backend-fastapi-dev`。
- 修改数据库表、SQLAlchemy 模型、Alembic migration、PostgreSQL 查询：使用 `postgres-migration-dev`。

这些 skill 都是本地开发专用内容，位于 `.local-skills/`，不提交到 GitHub。

## 验证清单

根据改动范围选择运行：

```bash
.venv/bin/python -m compileall apps/api/app
npm --prefix apps/web run typecheck
npm run db:migrate -- --sql
```

代码自检：

- 新增或修改 `apps/api`、`apps/web` 时，检查关键逻辑是否有必要注释。
- 注释应解释业务意图、边界和非显然逻辑，不做逐行翻译。
- 如果逻辑足够直观，可以不强行加注释，但命名必须清晰。

如果 Docker 正在运行，也验证：

```bash
docker compose up -d postgres
npm run db:migrate
npm run dev:api
npm run dev:web
```

## 约束

- 不要重新引入 SQLite 作为主数据库。
- 不要提交 `.local-skills/`。
- 不要在前端可读取的持久化存储或 Markdown 导出中暴露 API Key。
- 用户侧 skill 应放在 `skills/`，不要放在 `.local-skills/`。
- 本地开发专用说明不要写进用户侧产品 skill。
