# 前后端 Spec 拆分审查

## 1. 审查目标

本文档用于记录当前一期 spec 文件是否需要拆分为前端页面 spec 和后端接口 spec。

结论原则：

- 不要求每个功能都同时创建前端 spec 和后端 spec。
- 前端 spec 保留页面布局、交互、状态、表单校验和 API 依赖。
- 后端 spec 承载接口合同、数据库写入边界、service 业务规则、状态传播、模型调用和安全边界。
- 如果前端 spec 中只是简单列出 API 依赖表，可以保留；如果已经描述后端实现规则、数据库策略或复杂接口合同，应拆出或补充后端 spec。

## 2. 当前审查结论

| 文档 | 当前类型 | 结论 | 处理建议 |
| --- | --- | --- | --- |
| `frontend-specs/project-management.md` | 前端页面 spec | 暂不需要拆分 | 当前主要描述项目列表、创建页和基础信息编辑入口。API 依赖较简单，可继续保留在前端 spec。后续如果修改项目校验、下游状态传播或数据库字段，再新增后端 spec。 |
| `frontend-specs/project-workbench.md` | 前端页面 spec | 已拆分 | 资产快照接口已经拆到 `backend-specs/project-workbench-assets.md`。前端 spec 中保留 API 依赖表和页面验收，数据与迁移说明已改为引用后端 spec。 |
| `backend-specs/project-workbench-assets.md` | 后端接口 spec | 保持 | 该文档符合后端 spec 边界，包含快照隔离、接口定义、数据对象和前端 service 对齐。 |
| `frontend-specs/world-book-library.md` | 前端页面 spec | 已拆分 | 已新增 `backend-specs/world-book-library.md`。前端 spec 保留页面布局、字段控件、交互状态和 API 依赖表。 |
| `frontend-specs/character-card-library.md` | 前端页面 spec | 已拆分 | 已新增 `backend-specs/character-card-library.md`。前端 spec 保留页面布局、表单交互、错误展示和 API 依赖表。 |
| `frontend-specs/model-api-settings.md` | 前端页面 spec | 已拆分 | 已新增 `backend-specs/model-api-settings.md`。前端 spec 保留设置页交互，软删除、测试日志、API Key 安全和生成拦截以后端 spec 为准。 |

## 3. 优先级建议

### 已完成拆分

- `model-api-settings`
- `character-card-library`
- `world-book-library`
- `project-workbench-assets`

### 暂不拆分

- `project-management`
  - 原因：当前前端 spec 中 API 依赖较轻，主要是页面流程。项目时长校验和下游状态传播如果后续继续扩展，再补后端 spec。

## 4. 拆分方式

后续补后端 spec 时，不需要删除前端 spec 中的 API 依赖表。

推荐处理：

1. 在后端 spec 中定义完整接口合同、schema、错误规则和数据库边界。
2. 在前端 spec 的 API 依赖章节保留简表。
3. 在前端 spec 中增加一句：

```text
接口合同以后端接口 Spec 为准；本节仅描述页面依赖关系。
```

4. 把前端 spec 中明显属于后端实现的段落迁移到后端 spec，例如：
   - 数据库软删除策略。
   - 测试日志保留策略。
   - 快照隔离和状态传播。
   - 旧字段兼容保存规则。
   - 模型 API 调用协议和安全边界。

## 5. 后续执行规则

新增功能或修改现有功能时，按以下规则处理：

```text
只改页面表现
 -> 更新 frontend-specs

只改接口、数据库或服务规则
 -> 更新 backend-specs

同时影响页面和接口
 -> 同时更新 frontend-specs 和 backend-specs

影响产品范围
 -> 同步更新 module-prds
```

该审查文档只记录当前拆分状态，不替代具体模块的 PRD 或 spec。
