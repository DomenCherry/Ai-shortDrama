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
- 单功能产品需求：更新或新增 `docs/phase-1/module-prds/<feature>.md`。
- 后端接口、数据库或 service 规则变化：更新或新增 `docs/phase-1/backend-specs/<feature>.md`。
- 前端页面、表单或交互变化：更新或新增 `docs/phase-1/frontend-specs/<page>.md`。
- 技术或工程约束：更新 `docs/technical/`。

需求不清晰时，优先补产品文档，不直接进入代码实现。

### 3.2 编写或更新功能 PRD

功能 PRD 存放在：

```text
docs/phase-1/module-prds/<feature>.md
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

### 3.3 判断是否需要后端接口 Spec

后端接口 spec 不是每个功能都必须创建。只有本次需求影响后端接口、数据结构或服务规则时，才需要新增或更新。

以下情况必须更新后端接口 spec：

- 新增或修改后端 API。
- 修改请求体、响应体、字段校验或错误提示。
- 修改 Pydantic schema、SQLAlchemy 模型或 Alembic migration。
- 修改 service 层关键业务规则，例如软删除、快照隔离、版本保留、状态传播。
- 修改模型 API 调用规则、API Key 存储规则或生成任务前置条件。
- 前端需要依赖新的接口合同。

后端接口 spec 存放在：

```text
docs/phase-1/backend-specs/<feature>.md
```

后端接口 Spec 应说明：

- 接口路径和 HTTP 方法。
- 请求体、响应体和字段校验。
- 业务规则和状态传播。
- 数据库写入边界。
- 错误码和中文错误提示。
- 前端 service 方法对应关系。
- 验收标准。

后端接口 Spec 关注“接口如何被实现和调用”，不新增产品范围，也不替代前端页面 spec。

### 3.4 判断是否需要前端页面 Spec

前端页面 spec 也不是每次都必须创建。只有本次需求影响页面结构、用户流程、表单、交互或前端状态时，才需要新增或更新。

以下情况必须更新前端页面 spec：

- 新增页面。
- 重构页面。
- 修改页面入口、导航或用户流程。
- 修改表单字段、前端校验、按钮动作或错误提示。
- 增加复杂交互或多状态流程。
- 新增 AI 生成工作台页面。
- 页面依赖的 API 行为发生变化。

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
- 桌面端布局要求。
- 验收标准。

页面 spec 关注“页面如何呈现和交互”，不新增产品范围。

### 3.5 Spec 拆分原则

前端 spec 和后端 spec 按影响范围拆分，不做机械双写。

当前一期已有 spec 的拆分状态记录在：

```text
docs/technical/spec-splitting-review.md
```

判断规则：

```text
是否影响产品范围？
 -> 更新 module-prds

是否影响 API、数据库、service 规则、模型调用或安全边界？
 -> 更新 backend-specs

是否影响页面布局、表单、交互、状态或前端校验？
 -> 更新 frontend-specs

是否只是小 bug、文案或样式？
 -> 可只改代码，并在必要时同步相关 spec
```

前端 spec 可以保留“API 依赖”表，用来说明页面调用哪些前端方法和接口；但接口字段、数据库写入边界、状态传播和安全规则应以后端 spec 为准。

后端 spec 可以保留“前端 service 对齐”表，用来说明接口由哪些前端方法调用；但页面布局、按钮位置、交互状态和桌面端布局规则应以前端 spec 为准。

### 3.6 设计实现边界

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

### 3.7 后端实现

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

### 3.8 前端实现

前端实现遵守以下边界：

- 页面放在 `apps/web/app`。
- 前端 API 调用优先集中在 `apps/web/lib/api.ts`。
- 页面风格遵守 `docs/technical/frontend-style-guide.md`。
- 基础 UI 组件遵守 `docs/technical/ui-component-library.md`。
- 编码和注释遵守 `docs/technical/coding-standards.md`。

实现要求：

- 写页面或组件前，先查 `apps/web/components/ui` 是否已有基础控件，再查当前路由 `_components` 是否已有业务组件。
- 按钮、输入框、文本域、选择器、抽屉、标签、卡片、Tabs、Tooltip 等基础控件优先使用 `components/ui`，不要在页面内重复手写。
- 新增、删除或重命名 `components/ui` 组件时，必须同步更新 `docs/technical/ui-component-library.md`。
- 表单必须有前端校验。
- 后端错误必须转换为用户可理解的中文提示。
- 复杂状态必须显式展示，例如保存中、生成中、测试中、成功、失败。
- AI 生成操作必须有前置条件校验和失败重试入口。
- 复杂 React 状态、非显然交互和业务规则映射需要中文注释。

### 3.9 文档同步

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

### 3.10 验证与自检

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

- PRD、按需创建的后端接口 spec、页面 spec 和代码是否一致。
- 是否误改了不属于本次任务的文件。
- 是否保留了历史数据兼容。
- 是否有必要的中文注释。
- 是否没有泄露 API Key。
- 是否运行了与改动范围匹配的验证命令。

## 4. 推荐产物顺序

新增完整功能时，推荐顺序如下：

```text
1. docs/phase-1/module-prds/<feature>.md
2. 按需创建或更新 docs/phase-1/backend-specs/<feature>.md
3. 按需创建或更新 docs/phase-1/frontend-specs/<page>.md
4. apps/api 后端接口、服务、模型、迁移
5. apps/web 前端页面、API service、表单和状态
6. docs/README.md 或相关索引同步
7. 验证命令和人工检查
```

如果功能只涉及前端页面，可只更新页面 spec；如果功能只涉及后端接口或数据库，可只更新后端 spec。两类 spec 的创建由影响范围决定。

## 5. 文档边界速查

```text
project
  项目长期方向、背景、路线图

phase-1/prd.md
  第一期整体范围

phase-1/module-prds
  单功能模块 PRD

phase-1/backend-specs
  后端接口 Spec

phase-1/frontend-specs
  前端页面 Spec

technical
  架构、流程、编码、调试、风格等工程规范
```

## 6. 不符合流程的处理

如果用户直接要求实现代码，但缺少 PRD、后端接口 spec 或页面 spec，应按影响范围处理：

- 小 bug 或简单修复：可以直接修复，并在最终说明中指出不需要新增文档。
- 新增功能或复杂交互：先补齐模块 PRD 和受影响的 spec，再实现代码。
- 涉及数据库或 API 合同变化：先明确数据对象和接口边界，再实现。
- 涉及 AI 生成上下文变化：先明确输入来源、引用优先级、输出结构和验收标准。

流程的目标不是增加文档成本，而是让需求和实现保持一致。
