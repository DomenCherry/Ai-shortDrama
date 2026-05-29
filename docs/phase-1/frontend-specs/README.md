# 第一期前端页面 Spec

本目录用于存放第一期页面级前端 spec。

前端页面 spec 用于在实现页面前明确页面目标、布局、字段、交互状态、API 依赖、错误提示、响应式要求和验收标准。

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

- [角色卡库页面组](./character-card-library.md)

## 模板

创建页面 spec 时参考：

```text
docs/technical/frontend-page-spec-template.md
```
