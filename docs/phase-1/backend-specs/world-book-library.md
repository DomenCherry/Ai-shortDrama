# 后端接口 Spec：世界观库

## 1. 适用范围

本文档定义世界观库涉及的后端接口合同和服务规则。

覆盖能力：

- 世界观列表查询。
- 世界观创建、详情、更新、归档、激活。
- 世界观条目查询、创建、更新、启用、停用。
- 世界观加载到项目的后端依赖说明。

不覆盖能力：

- 项目内世界观快照 CRUD，详见 [项目工作台资产快照后端 Spec](./project-workbench-assets.md)。
- 世界观版本差异对比。
- 关键词自动触发算法。
- 世界观模板市场或多人共享。

## 2. 核心后端规则

### 2.1 世界观资产边界

世界观库只保存跨项目稳定的世界设定：

- 题材。
- 时代背景。
- 核心世界规则。
- 组织。
- 地点。
- 社会结构。
- 禁忌或限制。
- 整体风格。
- 结构化世界观条目。

世界观被加载到项目后，项目生成任务应读取项目内快照，不直接读取资产库原始内容。

### 2.2 状态规则

世界观状态：

- `draft`：草稿。
- `active`：可加载。
- `archived`：已归档。

世界观条目状态：

- `active`：可被加载和引用。
- `disabled`：不参与项目快照和生成引用。

规则：

- 只有 `active` 世界观可以加载到项目。
- 加载世界观时只复制 `active` 条目。
- 已归档世界观不再作为新项目候选。
- 第一版使用归档代替硬删除。

### 2.3 版本规则

以下内容变化时应提升世界观版本：

- 时代背景。
- 核心世界规则。
- 组织。
- 地点。
- 社会结构。
- 禁忌或限制。
- 整体风格。
- 世界观条目新增、更新、启用或停用。

项目快照保存加载时的来源版本。原始世界观更新不自动覆盖已加载项目。

### 2.4 项目加载规则

世界观加载到项目时：

- 后端必须复制世界观基础信息为 `ProjectWorldSnapshot`。
- 后端必须复制当前 `active` 世界观条目为条目快照内容。
- 后端必须记录来源世界观 ID、来源版本和加载时间。
- 每个项目最多只能有一个世界观快照。
- 项目内世界观快照更新不得修改 `WorldBook` 或 `WorldEntry`。

项目快照接口详见 [项目工作台资产快照后端 Spec](./project-workbench-assets.md)。

## 3. 数据对象

### 3.1 WorldBook

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 世界观 ID |
| name | string | 世界观名称 |
| genre | string | 题材类型 |
| era_background | string | 时代背景 |
| world_rules | string | 核心世界规则 |
| organizations | string | 主要组织 |
| locations | string | 主要地点 |
| social_structure | string | 社会结构或势力关系 |
| taboo_or_constraints | string | 禁忌、限制或不可违反的设定 |
| tone_style | string | 整体风格 |
| summary | string | 短摘要 |
| version | number | 版本号 |
| status | draft / active / archived | 状态 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.2 WorldBookCreate / Update

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 世界观名称 |
| genre | string | 是 | 题材类型 |
| era_background | string | 否 | 时代背景 |
| world_rules | string | 是 | 核心世界规则 |
| organizations | string | 否 | 主要组织 |
| locations | string | 否 | 主要地点 |
| social_structure | string | 否 | 社会结构 |
| taboo_or_constraints | string | 否 | 禁忌或限制 |
| tone_style | string | 否 | 整体风格 |
| summary | string | 否 | 摘要 |
| status | draft / active / archived | 是 | 状态 |

### 3.3 WorldEntry

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 条目 ID |
| world_book_id | string | 所属世界观 ID |
| title | string | 条目标题 |
| entry_type | string | 条目类型 |
| keywords | string | 关键词 |
| content | string | 条目正文 |
| applicable_scope | string | 适用范围 |
| priority | integer | 优先级 |
| status | active / disabled | 状态 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.4 WorldEntryCreate / Update

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| title | string | 是 | 条目标题 |
| entry_type | string | 是 | 条目类型 |
| keywords | string | 否 | 关键词 |
| content | string | 是 | 条目正文 |
| applicable_scope | string | 否 | 适用范围 |
| priority | integer | 是 | 优先级 |
| status | active / disabled | 是 | 状态 |

## 4. 接口定义

### 4.1 查询世界观列表

```text
GET /api/world-books
```

查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| search | string | 世界观名称搜索 |
| genre | string | 题材筛选 |
| status | draft / active / archived | 状态筛选 |

响应：

- `200`：`WorldBook[]` 摘要列表。

### 4.2 创建世界观

```text
POST /api/world-books
```

响应：

- `200`：新建的 `WorldBook`。
- `400`：字段非法。

业务要求：

- 必填字段：世界观名称、题材类型、核心世界规则、状态。
- 创建后版本号从 1 开始。

### 4.3 获取世界观详情

```text
GET /api/world-books/{world_book_id}
```

响应：

- `200`：`WorldBook`。
- `404`：世界观不存在。

### 4.4 更新世界观

```text
PUT /api/world-books/{world_book_id}
```

响应：

- `200`：更新后的 `WorldBook`。
- `400`：字段非法。
- `404`：世界观不存在。

业务要求：

- 修改影响生成上下文的字段时提升版本号。
- 不自动同步到已加载项目。

### 4.5 归档世界观

```text
POST /api/world-books/{world_book_id}/archive
```

响应：

- `200`：归档后的 `WorldBook`。
- `404`：世界观不存在。

业务要求：

- 设置 `status = archived`。
- 不物理删除世界观。
- 不删除历史项目快照来源。

### 4.6 激活世界观

```text
POST /api/world-books/{world_book_id}/activate
```

响应：

- `200`：激活后的 `WorldBook`。
- `400`：世界观缺少可加载所需字段。
- `404`：世界观不存在。

业务要求：

- 激活前必须校验世界观名称、题材类型和核心世界规则。
- 设置 `status = active`。

### 4.7 查询世界观条目

```text
GET /api/world-books/{world_book_id}/entries
```

响应：

- `200`：`WorldEntry[]`。
- `404`：世界观不存在。

### 4.8 创建世界观条目

```text
POST /api/world-books/{world_book_id}/entries
```

响应：

- `200`：新建的 `WorldEntry`。
- `400`：字段非法。
- `404`：世界观不存在。

业务要求：

- 必填字段：条目标题、条目类型、条目正文、优先级、状态。
- 创建成功后提升所属世界观版本号。

### 4.9 更新世界观条目

```text
PUT /api/world-books/{world_book_id}/entries/{entry_id}
```

响应：

- `200`：更新后的 `WorldEntry`。
- `400`：字段非法。
- `404`：世界观或条目不存在。

业务要求：

- 条目必须属于当前世界观。
- 更新成功后提升所属世界观版本号。

### 4.10 停用世界观条目

```text
POST /api/world-books/{world_book_id}/entries/{entry_id}/disable
```

响应：

- `200`：停用后的 `WorldEntry`。
- `404`：世界观或条目不存在。

业务要求：

- 设置 `status = disabled`。
- 停用成功后提升所属世界观版本号。
- 停用条目不参与后续项目加载快照。

### 4.11 启用世界观条目

```text
POST /api/world-books/{world_book_id}/entries/{entry_id}/enable
```

响应：

- `200`：启用后的 `WorldEntry`。
- `404`：世界观或条目不存在。

业务要求：

- 设置 `status = active`。
- 启用成功后提升所属世界观版本号。

## 5. 前端 Service 对齐

| 前端方法 | 后端接口 |
| --- | --- |
| `listWorldBooks` | `GET /api/world-books` |
| `createWorldBook` | `POST /api/world-books` |
| `getWorldBook` | `GET /api/world-books/{world_book_id}` |
| `updateWorldBook` | `PUT /api/world-books/{world_book_id}` |
| `archiveWorldBook` | `POST /api/world-books/{world_book_id}/archive` |
| `activateWorldBook` | `POST /api/world-books/{world_book_id}/activate` |
| `listWorldEntries` | `GET /api/world-books/{world_book_id}/entries` |
| `createWorldEntry` | `POST /api/world-books/{world_book_id}/entries` |
| `updateWorldEntry` | `PUT /api/world-books/{world_book_id}/entries/{entry_id}` |
| `disableWorldEntry` | `POST /api/world-books/{world_book_id}/entries/{entry_id}/disable` |
| `enableWorldEntry` | `POST /api/world-books/{world_book_id}/entries/{entry_id}/enable` |

项目加载接口见 [项目工作台资产快照后端 Spec](./project-workbench-assets.md)。

## 6. 验收标准

- 用户可以创建、查询、更新世界观。
- 必填字段缺失时返回中文错误。
- 用户可以归档和激活世界观。
- 用户可以新增、更新、启用、停用世界观条目。
- 条目新增、更新、启用、停用会提升所属世界观版本。
- 只有 `active` 世界观可以被加载到项目。
- 加载世界观到项目时只复制 `active` 条目。
- 世界观原始内容更新不自动覆盖项目快照。
- 已归档世界观不物理删除历史来源。
