# 后端接口 Spec：项目工作台资产快照

## 1. 适用范围

本文档定义项目工作台"项目资料 / 资产"入口中世界观与角色快照涉及的后端接口合同。

覆盖能力：

- 查询项目世界观快照。
- 加载世界观到项目。
- 更新项目世界观快照，用于项目内微调。
- 移除项目世界观快照。
- 查询项目角色快照。
- 加载角色卡到项目。
- 更新项目角色快照，用于项目内微调。
- 移除项目角色快照。

不覆盖能力：

- 世界观库原始资产 CRUD。
- 角色卡库原始资产 CRUD。
- 项目内快照与来源资产的复杂差异对比。
- 资产库新版本自动同步到项目快照。

## 2. 核心后端规则

### 2.1 快照隔离

- 世界观和角色卡加载到项目后，后端必须创建项目内快照。
- 项目内快照更新只修改项目快照表，不得更新 `WorldBook`、`WorldEntry` 或 `CharacterCard` 原始资产。
- 生成任务应优先读取项目快照，不直接读取资产库原始内容。

### 2.2 项目世界观限制

- 每个项目最多只能存在一个 `ProjectWorldSnapshot`。
- `load_mode = "new"` 时，如果项目已有世界观快照，后端必须拒绝请求。
- `load_mode = "replace"` 时，必须提供 `replace_snapshot_id`，且该快照必须属于当前项目。
- 只有 `active` 世界观可以加载到项目。
- 更新项目世界观快照时，只允许更新快照字段和条目快照内容，不允许修改来源世界观原始内容。

### 2.3 项目角色限制

- 每个项目可以存在多个 `ProjectCharacterSnapshot`。
- 同一 `source_character_card_id` 在同一项目内只能存在一个快照。
- `load_mode = "new"` 时，如果同一角色卡已加载到当前项目，后端必须拒绝请求。
- `load_mode = "replace"` 时，必须提供 `replace_snapshot_id`，且该快照必须属于当前项目。
- 只有 `active` 角色卡可以加载到项目。
- 更新项目角色快照时，只允许更新项目角色快照字段，不允许修改来源角色卡原始内容。

### 2.4 下游状态传播

以下操作成功后，后端应将已存在的下游创作内容标记为 `needs_review`：

- 新增加载项目世界观。
- 替换项目世界观。
- 更新项目世界观微调内容。
- 移除项目世界观。
- 新增加载项目角色。
- 替换项目角色。
- 更新项目角色微调内容。
- 移除项目角色。

下游范围包括：

- 故事文本：整体故事大纲、分集大纲、单集内容。
- 短剧制作：单集剧本、分镜、文案。

## 3. 数据对象

### 3.1 ProjectWorldSnapshot

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 项目世界观快照 ID |
| project_id | string | 所属项目 ID |
| source_world_book_id | string | 来源世界观 ID |
| source_version | number | 来源世界观加载时版本 |
| name | string | 项目内世界观名称，可微调 |
| genre | string | 项目内题材类型，可微调 |
| snapshot_content | string | 世界观基础信息快照，JSON 字符串或后续结构化 JSON |
| entry_snapshot_content | string | 世界观条目快照，JSON 字符串或后续结构化 JSON |
| loaded_at | string | 加载时间 |
| updated_at | string | 更新时间 |

### 3.2 ProjectWorldSnapshotUpdate

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 项目内世界观名称 |
| genre | string | 是 | 项目内题材类型 |
| snapshot_content | string | 是 | 项目内世界观基础信息快照 |
| entry_snapshot_content | string | 是 | 项目内世界观条目快照 |

### 3.3 ProjectCharacterSnapshot

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 项目角色快照 ID |
| project_id | string | 所属项目 ID |
| source_character_card_id | string | 来源角色卡 ID |
| source_version | number | 来源角色卡加载时版本 |
| name | string | 项目内角色名，可微调 |
| gender | 男 / 女 | 项目内角色性别 |
| role_type | string | 项目内人物原型或项目角色定位 |
| snapshot_content | string | 项目内角色设定快照，JSON 字符串或后续结构化 JSON |
| visual_description | string | 项目内视觉描述 |
| reference_image_url | string | 参考图 URL |
| reference_local_path | string | 参考图本地路径 |
| loaded_at | string | 加载时间 |
| updated_at | string | 更新时间 |

### 3.4 ProjectCharacterSnapshotUpdate

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 项目内角色名 |
| gender | 男 / 女 | 是 | 项目内角色性别 |
| role_type | string | 是 | 项目内人物原型或项目角色定位 |
| snapshot_content | string | 是 | 项目内角色设定快照 |
| visual_description | string | 否 | 项目内视觉描述 |
| reference_image_url | string | 否 | 参考图 URL |
| reference_local_path | string | 否 | 参考图本地路径 |

## 4. 接口定义

### 4.1 查询项目世界观快照

```text
GET /api/projects/{project_id}/world-snapshots
```

响应：

- `200`：`ProjectWorldSnapshot[]`。
- 第一版业务上最多返回 1 条。
- `404`：项目不存在。

### 4.2 加载世界观到项目

```text
POST /api/projects/{project_id}/world-snapshots
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| source_world_book_id | string | 是 | 来源世界观 ID |
| load_mode | new / replace | 否 | 默认 `new` |
| replace_snapshot_id | string | 否 | 替换时必填 |

响应：

- `200`：创建或替换后的 `ProjectWorldSnapshot`。
- `400`：世界观不是 `active`、项目已有世界观且使用 `new`、替换参数缺失。
- `404`：项目、世界观或被替换快照不存在。

错误提示：

- 项目不存在。
- 世界观不存在。
- 只有可加载状态的世界观可以加入项目。
- 每个项目只能加载一个世界观，请先移除或替换当前项目世界观。
- 替换世界观时必须提供项目内世界观快照 ID。
- 要替换的项目世界观不存在。

### 4.3 更新项目世界观快照

```text
PUT /api/projects/{project_id}/world-snapshots/{snapshot_id}
```

请求体：`ProjectWorldSnapshotUpdate`。

响应：

- `200`：更新后的 `ProjectWorldSnapshot`。
- `400`：字段非法或内容为空。
- `404`：项目或快照不存在。

业务要求：

- 只更新 `ProjectWorldSnapshot`。
- 不更新 `WorldBook` 或 `WorldEntry`。
- 成功后标记下游内容为 `needs_review`。

### 4.4 移除项目世界观快照

```text
DELETE /api/projects/{project_id}/world-snapshots/{snapshot_id}
```

响应：

- `200`：`{ "ok": true }`。
- `404`：项目或快照不存在。

业务要求：

- 只删除项目快照。
- 不删除世界观库原始资产。
- 成功后标记下游内容为 `needs_review`。

### 4.5 查询项目角色快照

```text
GET /api/projects/{project_id}/character-snapshots
```

响应：

- `200`：`ProjectCharacterSnapshot[]`。
- `404`：项目不存在。

### 4.6 加载角色卡到项目

```text
POST /api/projects/{project_id}/character-snapshots
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| source_character_card_id | string | 是 | 来源角色卡 ID |
| load_mode | new / replace | 否 | 默认 `new` |
| replace_snapshot_id | string | 否 | 替换时必填 |

响应：

- `200`：创建或替换后的 `ProjectCharacterSnapshot`。
- `400`：角色卡不是 `active`、同一角色卡已加载、替换参数缺失。
- `404`：项目、角色卡或被替换快照不存在。

错误提示：

- 项目不存在。
- 角色卡不存在。
- 只有可加载状态的角色卡可以加入项目。
- 该角色卡已加载到项目，不能重复加载。
- 替换角色时必须提供项目内角色快照 ID。
- 要替换的项目角色不存在。

### 4.7 更新项目角色快照

```text
PUT /api/projects/{project_id}/character-snapshots/{snapshot_id}
```

请求体：`ProjectCharacterSnapshotUpdate`。

响应：

- `200`：更新后的 `ProjectCharacterSnapshot`。
- `400`：字段非法或内容为空。
- `404`：项目或快照不存在。

业务要求：

- 只更新 `ProjectCharacterSnapshot`。
- 不更新 `CharacterCard`。
- 成功后标记下游内容为 `needs_review`。

### 4.8 移除项目角色快照

```text
DELETE /api/projects/{project_id}/character-snapshots/{snapshot_id}
```

响应：

- `200`：`{ "ok": true }`。
- `404`：项目或快照不存在。

业务要求：

- 只删除项目角色快照。
- 不删除角色卡库原始资产。
- 成功后标记下游内容为 `needs_review`。

## 5. 前端 service 对齐

| 前端方法 | 后端接口 |
| --- | --- |
| `listProjectWorldSnapshots` | `GET /api/projects/{project_id}/world-snapshots` |
| `loadWorldBookToProject` | `POST /api/projects/{project_id}/world-snapshots` |
| `updateProjectWorldSnapshot` | `PUT /api/projects/{project_id}/world-snapshots/{snapshot_id}` |
| `deleteProjectWorldSnapshot` | `DELETE /api/projects/{project_id}/world-snapshots/{snapshot_id}` |
| `listProjectCharacterSnapshots` | `GET /api/projects/{project_id}/character-snapshots` |
| `loadCharacterCardToProject` | `POST /api/projects/{project_id}/character-snapshots` |
| `updateProjectCharacterSnapshot` | `PUT /api/projects/{project_id}/character-snapshots/{snapshot_id}` |
| `deleteProjectCharacterSnapshot` | `DELETE /api/projects/{project_id}/character-snapshots/{snapshot_id}` |

## 6. 验收标准

- 项目不存在时，所有项目快照接口返回中文错误。
- 每个项目最多只能通过 `new` 加载一个世界观。
- 同一角色卡不能通过 `new` 重复加载到同一项目。
- 世界观和角色卡只有 `active` 状态可以加载。
- 更新项目世界观快照不会修改世界观库原始内容。
- 更新项目角色快照不会修改角色卡库原始内容。
- 加载、替换、更新和删除项目快照后，下游已有创作内容标记为 `needs_review`。
- 前端 service 方法、请求体和响应体与本文档一致。
