# 后端接口 Spec：角色卡库

## 1. 适用范围

本文档定义角色卡库涉及的后端接口合同和服务规则。

覆盖能力：

- 角色卡列表查询。
- 角色卡创建、详情、更新、归档。
- 角色参考图上传。
- 人物三视图生成。
- 人物三视图确认。
- 角色卡加载到项目的后端依赖说明。

不覆盖能力：

- 项目内角色快照 CRUD，详见 [项目工作台资产快照后端 Spec](./project-workbench-assets.md)。
- 专业角色一致性训练。
- 多参考图版本管理。
- 多人协作和权限控制。

## 2. 核心后端规则

### 2.1 角色卡边界

角色卡库只保存跨项目稳定的人物资产：

- 角色名。
- 性别。
- 人物原型。
- 身份摘要。
- 背景。
- 性格。
- 核心欲望 / 人物执念。
- 口吻和常用表达。
- 视觉描述、形象关键词、参考图和三视图。

角色卡不承载具体项目剧情。人物关系、冲突点、反转秘密、情感弧线和剧情功能应在项目角色快照或项目人物设定中维护。

### 2.2 旧字段兼容

数据库中可保留旧版剧情字段：

- `motivation`
- `secret`
- `conflict_points`
- `relationship_notes`
- `emotional_arc`
- `story_function`

新建和编辑角色卡时，后端不得因为前端隐藏这些字段而清空旧值。三视图生成 prompt 不得读取这些旧版剧情字段。

### 2.3 状态规则

角色卡状态：

- `draft`：草稿。
- `active`：可加载。
- `archived`：已归档。

规则：

- 只有 `active` 角色卡可以加载到项目。
- `archived` 角色卡不再作为新项目候选。
- 第一版使用归档代替硬删除。
- 已归档角色卡仍保留历史项目来源追踪。

### 2.4 版本规则

以下内容变化时应提升角色卡版本：

- 核心身份。
- 人物原型。
- 核心欲望 / 人物执念。
- 口吻。
- 视觉描述。
- 形象关键词。
- 参考图。
- 已确认三视图。

项目快照保存加载时的来源版本，原始角色卡更新不自动覆盖已加载项目。

### 2.5 图片生成前置条件

生成人物三视图前必须满足：

- 存在当前角色卡。
- 角色名、性别、身份摘要、核心欲望 / 人物执念有效。
- 视觉描述或形象关键词至少填写一项。
- 存在启用且最近测试成功的图片模型配置。

如果使用参考图参与生成，还必须满足：

- 当前角色已上传可读取的参考图。
- 当前启用图片模型声明支持参考图输入。

三视图生成失败不得覆盖已确认视觉参考。

## 3. 数据对象

### 3.1 CharacterCard

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 角色卡 ID |
| name | string | 角色名 |
| gender | 男 / 女 | 性别 |
| role_type | string | 人物原型 |
| identity | string | 身份摘要 |
| background | string | 人物背景 |
| personality | string | 性格 |
| goal | string | 核心欲望 / 人物执念 |
| speech_style | string | 说话方式 |
| catchphrases | string | 常用表达 |
| visual_description | string | 视觉描述 |
| image_keywords | string | 形象关键词 |
| turnaround_prompt | string | 三视图提示词 |
| reference_image_url | string | 参考图 URL |
| reference_local_path | string | 参考图本地路径 |
| turnaround_image_url | string | 三视图图片 URL |
| turnaround_local_path | string | 三视图本地路径 |
| turnaround_confirmed | boolean | 三视图是否确认 |
| version | number | 版本号 |
| status | draft / active / archived | 状态 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

兼容字段可继续存在于数据库，但不作为新流程推荐输入。

### 3.2 CharacterCardCreate / Update

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 角色名 |
| gender | 男 / 女 | 是 | 性别 |
| role_type | string | 是 | 人物原型 |
| identity | string | 是 | 身份摘要 |
| goal | string | 是 | 核心欲望 / 人物执念 |
| background | string | 否 | 人物背景 |
| personality | string | 否 | 性格 |
| speech_style | string | 否 | 说话方式 |
| catchphrases | string | 否 | 常用表达 |
| visual_description | string | 否 | 视觉描述 |
| image_keywords | string | 否 | 形象关键词 |
| turnaround_prompt | string | 否 | 三视图提示词 |
| status | draft / active / archived | 是 | 状态 |

更新接口必须保留未出现在请求体中的旧版兼容字段。

### 3.3 CharacterReferenceImageUpload

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| filename | string | 是 | 原始文件名 |
| content_type | image/png / image/jpeg / image/webp | 是 | 图片类型 |
| data_url | string | 是 | base64 data URL |

限制：

- 仅支持 `png`、`jpg`、`jpeg`、`webp`。
- 单张不超过 10MB。
- 保存后返回可预览地址或本地路径。

### 3.4 CharacterTurnaroundGeneration

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| image_url | string | 生成图片 URL |
| local_path | string | 本地图片路径 |
| prompt_snapshot | string | 实际生成提示词快照 |
| reference_image_used | boolean | 是否使用参考图 |
| generation_version | number | 生成版本 |
| confirmed | boolean | 是否确认 |

## 4. 接口定义

### 4.1 查询角色卡列表

```text
GET /api/character-cards
```

查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| search | string | 角色名搜索 |
| gender | 男 / 女 | 性别筛选 |
| role_type | string | 人物原型筛选 |
| status | draft / active / archived | 状态筛选 |

响应：

- `200`：`CharacterCard[]` 摘要列表。

### 4.2 创建角色卡

```text
POST /api/character-cards
```

响应：

- `200`：新建的 `CharacterCard`。
- `400`：字段非法。

业务要求：

- 必填字段：角色名、性别、人物原型、身份摘要、核心欲望 / 人物执念。
- 性别只支持男、女。
- 新建流程不得写入旧版剧情字段。

### 4.3 获取角色卡详情

```text
GET /api/character-cards/{character_card_id}
```

响应：

- `200`：`CharacterCard`。
- `404`：角色卡不存在。

### 4.4 更新角色卡

```text
PUT /api/character-cards/{character_card_id}
```

响应：

- `200`：更新后的 `CharacterCard`。
- `400`：字段非法。
- `404`：角色卡不存在。

业务要求：

- 更新隐藏旧版剧情字段时必须保留原值。
- 修改核心字段、视觉字段或参考图时应提升版本号。
- 已归档角色卡第一版可查看；是否允许继续编辑由前端交互控制，但后端不得误删历史来源。

### 4.5 归档角色卡

```text
POST /api/character-cards/{character_card_id}/archive
```

响应：

- `200`：归档后的 `CharacterCard`。
- `404`：角色卡不存在。

业务要求：

- 设置 `status = archived`。
- 不物理删除角色卡。
- 不删除已有项目快照来源信息。

### 4.6 上传角色参考图

```text
POST /api/character-cards/{character_card_id}/reference-images
```

请求体：`CharacterReferenceImageUpload`。

响应：

- `200`：更新后的参考图信息。
- `400`：格式非法、文件过大或 data URL 无法解析。
- `404`：角色卡不存在。

业务要求：

- 图片保存到项目约定的本地素材区或后端可访问存储。
- 返回前端可预览的信息。
- 保存成功后更新角色卡参考图字段并提升版本号。

### 4.7 生成人物三视图

```text
POST /api/character-cards/{character_card_id}/turnaround-images
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| prompt | string | 否 | 用户手动调整后的三视图提示词 |
| use_reference_image | boolean | 否 | 是否尝试使用参考图 |

响应：

- `200`：`CharacterTurnaroundGeneration`。
- `400`：字段不足、图片模型不可用或参考图能力不满足。
- `404`：角色卡不存在。

业务要求：

- 生成 prompt 只读取可复用人物资产字段。
- 不读取旧版剧情字段。
- 生成失败不覆盖已确认三视图。
- 生成结果在用户确认前只作为候选图。

### 4.8 确认人物三视图

```text
POST /api/character-cards/{character_card_id}/turnaround-images/{image_id}/confirm
```

响应：

- `200`：确认后的视觉参考信息。
- `404`：角色卡或三视图结果不存在。

业务要求：

- 将目标三视图标记为确认。
- 保存确认图片地址、生成提示词、参考图来源和生成版本。
- 确认后可作为后续项目加载和视频生成参考素材。

## 5. Prompt 组装规则

三视图生成 prompt 必须包含：

- 固定三视图规范：同一角色、正面、侧面、背面、全身、统一服装、干净背景、适合作为短剧人物视觉参考。
- 角色名。
- 性别。
- 身份摘要。
- 视觉描述。
- 形象关键词。
- 人物原型。
- 性格。
- 核心欲望 / 人物执念。
- 用户手动填写的三视图补充提示词。
- 参考图说明。

不得包含：

- 深层动机。
- 人物秘密。
- 冲突点。
- 人物关系说明。
- 情感弧线。
- 剧情功能。
- 本地文件系统绝对路径。
- API Key 或内部错误信息。

## 6. 前端 Service 对齐

| 前端方法 | 后端接口 |
| --- | --- |
| `listCharacterCards` | `GET /api/character-cards` |
| `createCharacterCard` | `POST /api/character-cards` |
| `getCharacterCard` | `GET /api/character-cards/{character_card_id}` |
| `updateCharacterCard` | `PUT /api/character-cards/{character_card_id}` |
| `archiveCharacterCard` | `POST /api/character-cards/{character_card_id}/archive` |
| `uploadCharacterReferenceImage` | `POST /api/character-cards/{character_card_id}/reference-images` |
| `generateCharacterTurnaround` | `POST /api/character-cards/{character_card_id}/turnaround-images` |
| `confirmCharacterTurnaround` | `POST /api/character-cards/{character_card_id}/turnaround-images/{image_id}/confirm` |

项目加载接口见 [项目工作台资产快照后端 Spec](./project-workbench-assets.md)。

## 7. 验收标准

- 新建角色卡必须校验角色名、性别、人物原型、身份摘要、核心欲望 / 人物执念。
- 性别只允许男、女。
- 角色卡编辑不得清空旧版隐藏剧情字段。
- 三视图 prompt 不包含旧版剧情字段。
- 参考图上传限制格式和大小。
- 图片模型未配置或测试不可用时，三视图生成被阻止。
- 模型不支持参考图时，参考图参与生成被阻止并返回中文提示。
- 生成失败不覆盖已确认三视图。
- 归档角色卡不物理删除历史来源。
