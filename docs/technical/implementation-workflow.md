# 功能实现流程规范

## 1. 目标

本文档用于固化本项目从“提出需求”到“代码实现完成”的标准流程。

目标是避免需求、详细设计、页面 spec、代码和验证互相脱节，保证后续每个功能都能按照可追踪、可验证、可维护的方式推进。

## 2. 适用范围

以下情况必须遵守本文档：

- 新增一期功能模块。
- 修改已有功能的业务规则。
- 新增或重构前端页面。
- 新增或修改后端 API。
- 修改数据库模型或 Alembic migration。
- 调整 AI 生成流程、提示词上下文或模型调用规则。

小范围文案调整、简单样式修复、明显 bug 修复可以简化流程，但如果影响用户流程、字段含义、API 行为或数据结构，仍需补齐对应文档。

## 3. 标准流程

### 3.1 明确需求

先确认需求属于哪个层级：

- 项目长期方向：更新 `docs/project/`。
- 阶段整体范围：更新 `docs/phase-1/prd.md`。
- 单功能产品需求：更新或新增 `docs/phase-1/prds/<feature>-prd.md`。
- 单功能详细说明：更新或新增 `docs/phase-1/features/<feature>.md`。
- 前端页面实现：更新或新增 `docs/phase-1/frontend-specs/<page>.md`。
- 技术或工程约束：更新 `docs/technical/`。

需求不清晰时，优先补产品文档，不直接进入代码实现。

### 3.2 编写或更新功能 PRD

功能 PRD 存放在：

```text
docs/phase-1/prds/<feature>-prd.md
```

功能 PRD 应说明：

- 背景和问题。
- 产品目标。
- 用户与场景。
- 功能范围。
- 不做什么。
- 核心流程。
- 数据对象。
- 业务规则。
- 验收标准。

PRD 关注“为什么做、做什么、做到什么程度”，不展开具体页面布局和代码结构。

### 3.3 编写或更新功能说明 Spec

功能说明 Spec 存放在：

```text
docs/phase-1/features/<feature>.md
```

功能说明 Spec 应说明：

- 功能定位。
- 具体模块。
- 字段定义。
- 状态流转。
- 操作规则。
- 数据对象关系。
- 与其他功能的衔接。
- 边界和异常处理。

功能说明 Spec 关注“这个功能具体如何定义”，不替代 PRD，也不替代前端页面 spec。

### 3.4 编写或更新前端页面 Spec

新增页面、重构页面、复杂交互或 AI 生成工作台页面，必须先更新页面 spec。

页面 spec 存放在：

```text
docs/phase-1/frontend-specs/<page>.md
```

模板参考：

```text
docs/technical/frontend-page-spec-template.md
```

页面 spec 应说明：

- 页面目标。
- 用户流程。
- 信息架构。
- 布局结构。
- 字段、控件和校验。
- 交互状态。
- API 依赖。
- 错误提示。
- 响应式要求。
- 验收标准。

页面 spec 关注“页面如何呈现和交互”，不新增产品范围。

### 3.5 设计实现边界

进入代码前，需要确认本次是否涉及以下内容：

- 是否需要新增或修改后端 API。
- 是否需要新增或修改数据库字段。
- 是否需要 Alembic migration。
- 是否需要前端 API service。
- 是否需要页面、组件或表单状态。
- 是否影响已有数据兼容。
- 是否影响 API Key、模型配置或导出内容等安全边界。
- 是否需要同步更新 `rules/` 或 `skills/`。

如果涉及数据库结构变更，必须先确认 PostgreSQL 兼容性，再编写 Alembic migration。

### 3.6 后端实现

后端实现遵守以下边界：

- HTTP 路由放在 `apps/api/app/api`。
- 业务逻辑放在 `apps/api/app/services`。
- Pydantic schema 放在 `apps/api/app/models/schemas.py`。
- SQLAlchemy 模型放在 `apps/api/app/models/db_models.py`。
- 数据库迁移放在 `apps/api/alembic/versions`。

实现要求：

- route 层只处理请求响应边界，不堆复杂业务逻辑。
- service 层负责跨字段规则、状态流转、生成前置条件和数据兼容。
- 用户可见错误使用中文。
- API Key 不明文返回、不进入 Markdown 导出。
- 新增或修改关键业务逻辑时，必须添加有意义的中文注释。

### 3.7 前端实现

前端实现遵守以下边界：

- 页面放在 `apps/web/app`。
- 前端 API 调用优先集中在 `apps/web/lib/api.ts`。
- 页面风格遵守 `docs/technical/frontend-style-guide.md`。
- 编码和注释遵守 `docs/technical/coding-standards.md`。

实现要求：

- 表单必须有前端校验。
- 后端错误必须转换为用户可理解的中文提示。
- 复杂状态必须显式展示，例如保存中、生成中、测试中、成功、失败。
- AI 生成操作必须有前置条件校验和失败重试入口。
- 复杂 React 状态、非显然交互和业务规则映射需要中文注释。

### 3.8 文档同步

代码实现过程中，如果发现原文档与实际实现不一致，应同步修正文档。

需要同步的典型情况：

- 字段含义变化。
- 校验规则变化。
- API 行为变化。
- 页面流程变化。
- 模型调用策略变化。
- 数据兼容策略变化。
- 安全规则变化。

文档不是实现后的附属品，而是功能验收的一部分。

### 3.9 验证与自检

根据改动范围运行验证。

后端代码：

```bash
.venv/bin/python -m compileall apps/api/app
```

前端代码：

```bash
npm --prefix apps/web run typecheck
```

数据库迁移：

```bash
npm run db:migrate -- --sql
npm run db:migrate
```

文档检索：

```bash
rg -n "<关键功能名>|<关键字段名>" docs
```

完成前自检：

- PRD、功能说明、页面 spec 和代码是否一致。
- 是否误改了不属于本次任务的文件。
- 是否保留了历史数据兼容。
- 是否有必要的中文注释。
- 是否没有泄露 API Key。
- 是否运行了与改动范围匹配的验证命令。

## 4. 推荐产物顺序

新增完整功能时，推荐顺序如下：

```text
1. docs/phase-1/prds/<feature>-prd.md
2. docs/phase-1/features/<feature>.md
3. docs/phase-1/frontend-specs/<page>.md
4. apps/api 后端接口、服务、模型、迁移
5. apps/web 前端页面、API service、表单和状态
6. docs/README.md 或相关索引同步
7. 验证命令和人工检查
```

如果功能只涉及前端页面，可从第 3 步开始，但仍需确认 PRD 和功能说明没有缺口。

## 5. 文档边界速查

```text
project
  项目长期方向、背景、路线图

phase-1/prd.md
  第一期整体范围

phase-1/prds
  单功能产品 PRD

phase-1/features
  单功能详细说明 Spec

phase-1/frontend-specs
  前端页面 Spec

technical
  架构、流程、编码、调试、风格等工程规范
```

## 6. 不符合流程的处理

如果用户直接要求实现代码，但缺少 PRD、功能说明或页面 spec，应按影响范围处理：

- 小 bug 或简单修复：可以直接修复，并在最终说明中指出不需要新增文档。
- 新增功能或复杂交互：先补齐必要文档，再实现代码。
- 涉及数据库或 API 合同变化：先明确数据对象和接口边界，再实现。
- 涉及 AI 生成上下文变化：先明确输入来源、引用优先级、输出结构和验收标准。

流程的目标不是增加文档成本，而是让需求和实现保持一致。
