---
name: tdd-and-verification
description: 本地开发验证时使用。适用于新增功能、修复缺陷、调整 API 行为、修改数据库逻辑或前端交互。要求先定义可验证行为，再实现和运行对应检查。
---

# 测试驱动与完成前验证

## 使用场景

当修改会影响用户可见行为、API 合同、数据库结构或生成流程时使用。

## 工作流程

1. 明确行为：写清楚输入、输出、错误场景和验收标准。
2. 选择验证方式：优先选择最小但能证明行为正确的检查。
3. 实现或修改代码。
4. 运行验证。
5. 如果验证失败，先定位失败原因，再继续修改。
6. 最终说明运行过哪些验证、哪些验证受环境限制无法运行。

## 验证优先级

后端：

- Pydantic 校验是否符合 PRD。
- API 状态码和响应体是否符合前端需要。
- 数据库写入和读取是否一致。
- Alembic migration 是否能生成 PostgreSQL SQL。

前端：

- 表单校验是否阻止非法输入。
- API 错误是否展示为用户可理解的提示。
- 页面在移动和桌面宽度下不出现明显布局错位。
- TypeScript 检查通过。

## 当前项目基础检查

```bash
.venv/bin/python -m compileall apps/api/app
npm --prefix apps/web run typecheck
npm run db:migrate -- --sql
```

如果 Docker 和本地端口可用：

```bash
docker compose up -d postgres
npm run db:migrate
npm run dev:api
npm run dev:web
```

## 完成前必须说明

- 已运行的验证命令。
- 未运行的验证命令及原因。
- 是否修改了 API、schema、migration 或前端交互。

