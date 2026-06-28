---
name: frontend-nextjs-dev
description: 修改本项目 Next.js 前端时使用。适用于 apps/web 下的页面、表单、API 调用、React 状态、样式、前端验证、页面 spec 和页面风格一致性。强调先维护 docs/phase-1/frontend-specs/ 中的页面 spec，先检查 docs/technical/ui-component-library.md 和 components/ui，遵守 docs/technical/frontend-style-guide.md、类型安全、可用性和与后端 API 合同一致。
---

# Next.js 前端开发

## 使用场景

修改 `apps/web` 时使用，尤其是：

- 新增页面。
- 修改表单。
- 调整 API 调用。
- 增加校验或错误提示。
- 调整布局和样式。
- 需要保证不同页面视觉风格和交互模式一致。
- 需要新增或更新页面 spec。

## 项目约定

- 使用 Next.js App Router。
- 页面放在 `apps/web/app`。
- 通用 UI 组件放在 `apps/web/components/ui`，当前采用 shadcn/ui。
- 路由私有业务组件放在对应路由的 `_components`。
- 路由私有状态逻辑放在对应路由的 `_hooks`。
- 路由私有表单转换和工具函数放在对应路由的 `_utils`。
- API 客户端放在 `apps/web/lib`。
- 样式优先沿用 `apps/web/app/globals.css` 的现有变量和类。
- 页面风格必须遵守 `docs/technical/frontend-style-guide.md`。
- 基础 UI 组件必须遵守 `docs/technical/ui-component-library.md`。
- 前端代码注释必须遵守 `docs/technical/coding-standards.md`。
- 页面 spec 模板位于 `docs/technical/frontend-page-spec-template.md`。
- 第一期页面 spec 位于 `docs/phase-1/frontend-specs/`。
- 新增或修改按钮、输入框、文本域、选择器、抽屉、状态标签、卡片、Tabs、Tooltip 等基础控件时，必须先检查 `apps/web/components/ui`。
- 基础控件不得在页面内重复手写；只有现有组件无法满足时，才新增或扩展 UI 组件，并同步更新 `docs/technical/ui-component-library.md`。
- 页面语言使用中文。

## 页面 spec 要求

以下情况必须先创建或更新对应页面 spec，再修改代码：

- 新增页面。
- 重构页面。
- 增加复杂交互。
- 新增 AI 生成工作台页面。
- 改动页面流程、API 依赖或关键状态。

小范围样式修复、文案修正、局部 bug fix 可不新建 spec；但如果影响页面流程、接口调用、校验规则或用户可见状态，必须更新 spec。

页面 spec 必须说明：

- 页面目标和用户流程。
- 信息架构和布局结构。
- 字段、控件和校验规则。
- 交互状态和错误提示。
- API 依赖。
- 响应式要求。
- 验收标准。

## 实现要求

- 写前端代码前，先查 `docs/technical/ui-component-library.md`，再查 `apps/web/components/ui`，最后查当前路由 `_components`。
- 表单必须有前端即时校验。
- 后端错误必须展示为用户可理解的中文提示。
- API 请求类型应和后端 schema 对齐。
- 不把 API Key 放入 localStorage、URL、Markdown 导出或普通文本展示。
- 页面应能在窄屏下基本可用。

## 注释要求

- 复杂 React state、多状态互斥和用户可见状态切换必须加中文注释。
- 表单校验与后端业务规则一致时，需要注释说明对应业务约束。
- API 调用中涉及脱敏、安全、错误映射或重试保护时，需要注释说明原因。
- AI 生成工作台中的上下文选择、覆盖保护和结果确认流程需要注释。
- 明显 JSX 结构不需要注释，优先通过组件命名和结构表达。
- 避免逐行解释语法或重复变量名含义。

## 设计要求

- 工具型页面优先清晰、紧凑、可扫描。
- 不做营销式 landing page。
- 不使用大面积装饰图形。
- 不新增一次性页面风格；基础控件优先复用 `components/ui`，页面布局类优先复用 `.page-header`、`.panel`、`.stack`、`.grid-2`、`.field`、`.actions`、`.hint`、`.error`、`.success`。
- 按钮文案直接表达动作。
- 重要状态明确展示，例如保存中、测试中、创建成功、接口失败。
- 新增 AI 生成工作台页面时，应把生成结果拆成可扫描结构，而不是只展示一整段文本。

## 验证

```bash
npm --prefix apps/web run typecheck
```

完成前还要自检关键前端逻辑是否符合 `docs/technical/coding-standards.md` 的注释要求。

如本次新增或更新页面 spec，还应检查：

```bash
rg -n "页面目标|用户流程|API 依赖|验收标准" docs/phase-1/frontend-specs
```

如前端服务可启动，还应访问：

```text
http://127.0.0.1:3000
http://127.0.0.1:3000/settings
http://127.0.0.1:3000/projects/new
```
