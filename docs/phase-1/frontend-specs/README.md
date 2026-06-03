# 第一期前端页面 Spec

本目录用于存放第一期页面级前端 spec。

前端页面 spec 用于在实现页面前明确页面目标、布局、字段、交互状态、API 依赖、错误提示、响应式要求和验收标准。

前端页面 spec 按影响范围创建，不要求每个功能都同时创建后端 spec。如果需求只影响 API、数据库、service 规则、模型调用或安全边界，可只更新后端接口 spec。

## 使用规则

以下情况必须先创建或更新对应页面 spec：

- 新增页面。
- 重构页面。
- 增加复杂交互。
- 新增 AI 生成工作台页面。
- 改动页面流程、API 依赖或关键状态。

以下情况可不新增 spec，但如果影响页面流程仍需补充：

- 小范围样式修复。
- 文案修正。
- 局部 bug fix。

## 与后端 Spec 的边界

- 前端 spec 可以记录 API 依赖表，用于说明页面调用哪些前端方法和后端接口。
- 前端 spec 不定义数据库写入边界、后端状态传播、错误码或安全规则。
- 如果页面改动要求新增接口、修改请求/响应字段或改变后端业务规则，需要同步更新 `docs/phase-1/backend-specs/`。

## 命名约定

页面 spec 文件使用英文短横线命名：

```text
docs/phase-1/frontend-specs/<page-name>.md
```

示例：

- `settings.md`
- `project-creation.md`
- `project-workbench.md`

## 已有页面 Spec

- [项目管理](./project-management.md)
- [项目工作台](./project-workbench.md)
- [世界观库](./world-book-library.md)
- [角色卡库](./character-card-library.md)
- [模型 API 配置](./model-api-settings.md)

## 模板

创建页面 spec 时参考：

```text
docs/technical/frontend-page-spec-template.md
```
