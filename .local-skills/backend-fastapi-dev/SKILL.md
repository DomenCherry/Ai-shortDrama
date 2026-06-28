---
name: backend-fastapi-dev
description: 修改本项目 FastAPI 后端时使用。适用于 apps/api 下的路由、Pydantic schema、服务层、模型 API 配置、项目 API、错误处理和后端验证。
---

# FastAPI 后端开发

## 使用场景

修改 `apps/api` 时使用，尤其是：

- 新增或修改 API 路由。
- 修改 Pydantic schema。
- 修改 service 层业务逻辑。
- 调整错误码或错误信息。
- 接入模型 API 调用。

## 项目约定

- 路由放在 `apps/api/app/api`。
- 业务逻辑放在 `apps/api/app/services`。
- 请求和响应 schema 放在 `apps/api/app/models/schemas.py`。
- 数据库模型放在 `apps/api/app/models/db_models.py`。
- 数据库访问使用 SQLAlchemy session。
- 不在 route 层堆复杂业务逻辑。
- 后端代码注释遵守 `docs/technical/coding-standards.md`。

## API 设计要求

- 用户输入校验优先放在 Pydantic schema。
- 跨字段业务规则放在 service 层。
- 用户可见错误使用中文。
- API Key 不进入响应体明文。
- 生成任务前置条件失败时，应返回明确错误。

## 数据库要求

- 不使用 SQLite。
- 不手写裸 SQL，除非 SQLAlchemy 无法清晰表达且有必要。
- 表结构变更必须配套 Alembic migration。

## 注释要求

- 业务规则必须加中文注释，例如项目总时长限制、角色卡快照不回写原始资产。
- Pydantic 字段校验和跨字段校验需要说明校验意图。
- service 层中的状态流转、覆盖保护、生成前置条件和安全边界需要注释。
- 数据库模型中的版本字段、状态字段、历史保留策略和非显然关系需要注释。
- Alembic migration 中的兼容逻辑、默认值和不可逆操作需要注释。
- 避免逐行解释语法或重复函数名含义。

## 验证

```bash
.venv/bin/python -m compileall apps/api/app
```

完成前还要自检关键后端逻辑是否符合 `docs/technical/coding-standards.md` 的注释要求。

如数据库可用：

```bash
npm run db:migrate
```

如服务可启动：

```bash
npm run dev:api
curl http://127.0.0.1:8000/health
```
