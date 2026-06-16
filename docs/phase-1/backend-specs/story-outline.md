# 后端接口 Spec：整体故事大纲、AI 协助与参考故事结构抽取

## 1. 适用范围

本文档定义项目工作台“故事大纲”阶段涉及的后端接口合同、数据结构、模型调用规则和状态传播规则。

覆盖能力：

- 查询和保存正式整体故事大纲。
- 通过对话式 AI 协助补齐故事大纲字段草稿。
- 生成完整整体故事大纲。
- 局部改写整体故事大纲字段。
- 上传或粘贴参考故事文本。
- 使用独立结构抽取规则生成参考框架草稿。
- 校验参考框架草稿是否完成去具体化。
- 将校验通过的参考框架草稿应用到正式故事大纲。
- 应用正式故事大纲后标记下游内容为 `needs_review`。

不覆盖能力：

- PDF、Word、网页链接或图片 OCR 输入。
- 参考故事版权状态识别。
- 复杂版本对比和回滚。
- AI 协助创作对话记录持久化。
- 自动生成分集大纲、人物设定或剧本。

## 2. 核心后端规则

### 2.1 文本模型前置校验

AI 生成、AI 协助创作和参考故事结构抽取必须读取当前启用且最近测试成功的文本模型配置。

如果没有可用文本模型配置，接口返回 `400`，错误提示：

- 请先配置并测试成功文本生成模型 API。

### 2.2 故事大纲生成上下文

生成完整故事大纲时，后端应聚合以下上下文：

- 项目基础信息：创意描述、题材、平台、受众、风格、集数、单集时长、总时长。
- 已确认或已保存的选题方向。
- 项目内世界观快照。
- 项目内角色快照。
- 用户补充要求。
- 用户已应用的参考框架草稿。

项目内快照优先于资产库原始内容。用户手动保存过的正式故事大纲优先于历史 AI 生成结果。

### 2.3 参考故事结构抽取规则

参考故事结构抽取必须使用独立规则模板：

- `rules/story-structure-extraction-rule.md`

后端不得将参考故事输入交给普通摘要、普通改写或普通整体故事大纲生成 Prompt。普通整体故事大纲生成继续使用：

- `rules/story-outline-rule.md`

### 2.4 AI 协助创作规则

AI 协助创作必须使用独立规则模板：

- `rules/story-outline-assistant-rule.md`

后端不得将 AI 协助创作对话交给普通整体故事大纲生成 Prompt 或参考故事结构抽取 Prompt。

AI 协助接口只返回引导话术、字段补丁和完成状态，不写入 `ProjectStoryOutline`，不标记下游内容为 `needs_review`。只有前端后续调用正式故事大纲保存接口时，才触发正式保存和下游状态传播。

### 2.5 去具体化校验

参考框架草稿生成后，后端必须执行输出校验。

校验目标：

- 不包含参考故事中的角色、地点、组织、专有名词、经典桥段、对白或原文句子。
- 输出不是参考故事摘要或改写。
- 输出包含参考框架草稿的必需结构字段。

校验结果：

- `validation_status = "passed"`：可预览、可应用。
- `validation_status = "failed"`：可预览失败原因，但不得应用。
- `validation_status = "pending"`：生成或校验中，不得应用。

如果第一次校验失败，服务层应优先触发一次基于失败原因的重新去具体化。重试后仍失败时，保存失败草稿和失败原因，并阻止应用。

### 2.6 下游状态传播

以下操作成功后，后端应将已存在的下游内容标记为 `needs_review`：

- 保存正式整体故事大纲。
- 生成完整故事大纲并写入正式大纲。
- 局部改写并写入正式大纲。
- 应用参考框架草稿到正式故事大纲。
- AI 协助创作确认保存正式故事大纲。

下游范围：

- 分集大纲。
- 单集故事正文。
- 单集剧本。
- 分镜。
- 文案。

仅上传参考故事、生成参考框架草稿、进入 AI 协助创作页、发送 AI 协助对话或更新页面草稿，不标记下游内容。

## 3. 数据对象

### 3.1 ProjectStoryOutline

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 故事大纲 ID |
| project_id | string | 所属项目 ID，每个项目最多一条正式大纲 |
| logline | string | 一句话故事 |
| story_background | string | 故事背景 |
| main_goal | string | 主线目标 |
| core_conflict | string | 核心矛盾 |
| story_start | string | 故事起点 |
| plot_structure | string | 起承转合结构 |
| reversals | string | 阶段性反转 |
| emotion_curve | string | 情绪曲线 |
| foreshadowing | string | 关键伏笔 |
| character_arcs | string | 人物弧光 |
| ending_direction | string | 结局方向 |
| pacing_advice | string | 整体节奏建议 |
| capacity_advice | string | 与集数和总时长匹配的剧情容量建议 |
| notes | string | 补充说明 |
| status | draft / confirmed / needs_review | 产物状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

兼容要求：

- 当前实现已有 `logline`、`core_conflict`、`main_goal`、`character_arcs`、`ending_direction`、`notes` 和 `status` 字段。
- 新字段应通过迁移新增为可空字段，避免破坏已有项目。

### 3.2 ReferenceStoryStructureDraft

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 参考框架草稿 ID |
| project_id | string | 所属项目 ID |
| source_type | pasted / uploaded | 输入来源 |
| source_filename | string | 上传文件名，粘贴输入为空 |
| source_text_excerpt | string | 参考文本摘录，用于用户识别来源，不保存完整原文到响应 |
| story_type | string | 故事类型 |
| goal_model | string | 主线目标模型 |
| inciting_event_type | string | 起点事件类型 |
| conflict_model | string | 核心冲突模型 |
| stage_structure | string | 阶段结构 |
| reversal_mechanism | string | 反转机制 |
| emotion_curve | string | 情绪曲线 |
| foreshadowing_pattern | string | 伏笔与回收方式 |
| ending_pattern | string | 结局模式 |
| adaptation_advice | string | 可迁移的短剧改编建议 |
| de_specificity_notes | string | 去具体化说明 |
| validation_status | pending / passed / failed | 去具体化校验状态 |
| validation_notes | string | 校验说明或失败原因 |
| status | draft / applied / discarded | 草稿状态 |
| outline_preview | ProjectStoryOutlinePayload | 后端按正式故事大纲字段映射出的可编辑预览，不自动写入正式大纲 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.3 StoryOutlineAssistResult

AI 协助创作接口返回的临时结果，不落库。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| assistant_message | string | AI 面向用户的下一步引导话术 |
| outline_patch | Partial<ProjectStoryOutlinePayload> | 本轮建议填充或修改的故事大纲字段补丁，不包含 `status` |
| completion.required_fields | string[] | 必填字段 key，固定为故事核心层和结构规划层字段 |
| completion.completed_fields | string[] | 已完成的必填字段 key |
| completion.missing_fields | string[] | 未完成的必填字段 key |
| completion.is_complete | boolean | 必填字段是否全部完成 |
| field_notes | object | 字段更新原因，key 为字段名 |
| next_focus_fields | string[] | 下一轮建议关注的字段 |

## 4. 接口定义

### 4.1 查询正式故事大纲

```text
GET /api/projects/{project_id}/story-outline
```

响应：

- `200`：`ProjectStoryOutline | null`。
- `404`：项目不存在。

### 4.2 保存正式故事大纲

```text
PUT /api/projects/{project_id}/story-outline
```

请求体：`ProjectStoryOutlinePayload`。

响应：

- `200`：保存后的 `ProjectStoryOutline`。
- `400`：字段非法或状态非法。
- `404`：项目不存在。

业务要求：

- 空字符串统一保存为 `null`。
- `status` 只允许 `draft`、`confirmed`、`needs_review`。
- 成功后更新项目 `updated_at`。
- 成功后标记下游内容为 `needs_review`。

### 4.3 生成完整故事大纲

```text
POST /api/projects/{project_id}/story-outline/generate
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| user_requirements | string | 否 | 用户补充要求 |
| reference_draft_id | string | 否 | 已校验通过的参考框架草稿 ID |
| write_mode | preview / apply | 否 | 默认 `preview` |

响应：

- `200`：`StoryOutlineGenerationResult`。
- `400`：文本模型不可用、参考框架未通过校验、字段非法。
- `404`：项目或参考框架草稿不存在。

`StoryOutlineGenerationResult`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| outline | ProjectStoryOutlinePayload | 生成的大纲字段 |
| applied | boolean | 是否已写入正式故事大纲 |
| saved_outline | ProjectStoryOutline | `write_mode=apply` 时返回 |
| context_summary | string | 本次生成使用的上下文摘要 |

业务要求：

- `preview` 只返回生成结果，不写入数据库，不标记下游内容。
- `apply` 写入正式故事大纲，并标记下游内容为 `needs_review`。
- 如果传入 `reference_draft_id`，该草稿必须属于当前项目，且 `validation_status = "passed"`。

### 4.4 局部改写故事大纲

```text
POST /api/projects/{project_id}/story-outline/rewrite
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| field | string | 是 | 要改写的大纲字段 |
| current_value | string | 是 | 当前字段内容 |
| instruction | string | 是 | 改写要求 |
| write_mode | preview / apply | 否 | 默认 `preview` |

响应：

- `200`：`StoryOutlineRewriteResult`。
- `400`：字段不允许改写、文本模型不可用。
- `404`：项目不存在或正式大纲不存在。

可改写字段：

- `story_background`
- `main_goal`
- `core_conflict`
- `plot_structure`
- `reversals`
- `emotion_curve`
- `foreshadowing`
- `ending_direction`
- `pacing_advice`
- `capacity_advice`
- `notes`

业务要求：

- `preview` 只返回改写内容。
- `apply` 写回对应字段并标记下游内容为 `needs_review`。

### 4.5 AI 协助创作故事大纲

```text
POST /api/projects/{project_id}/story-outline/assist
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| action | start / reply | 是 | 启动引导或回复用户输入 |
| current_outline | ProjectStoryOutlinePayload | 是 | 当前页面字段草稿 |
| messages | Message[] | 是 | 当前页面内已有对话历史 |
| user_message | string | reply 必填 | 用户当前轮回复 |

`Message`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| role | user / assistant | 消息角色 |
| content | string | 消息内容 |

响应：

- `200`：`StoryOutlineAssistResult`。
- `400`：文本模型不可用、回复内容为空、模型响应格式非法。
- `404`：项目不存在。

业务要求：

- 后端必须使用 `rules/story-outline-assistant-rule.md` 作为 system prompt。
- 接口必须聚合项目基础信息、世界观快照、角色快照、当前字段草稿、对话历史和用户当前回复。
- `outline_patch` 只允许返回故事大纲文本字段，不允许返回 `status`、`id`、`project_id`、时间字段或下游字段。
- 必填字段为故事核心层和结构规划层字段；执行辅助层字段不阻塞 `completion.is_complete`。
- `completion` 只用于前端展示完成度和待补充字段，不作为正式故事大纲保存接口的硬性拦截条件。
- 接口只返回草稿建议，不写入正式故事大纲，不触发下游 `needs_review`。

### 4.6 抽取参考故事结构

```text
POST /api/projects/{project_id}/story-structure-drafts/extract
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| source_type | pasted / uploaded | 是 | 输入来源 |
| source_filename | string | uploaded 必填 | 原文件名 |
| source_text | string | 是 | 参考故事文本 |
| user_requirements | string | 否 | 用户补充抽取要求 |

响应：

- `200`：`ReferenceStoryStructureDraft`。
- `400`：文本模型不可用、文件类型非法、参考文本为空、校验失败且无可用草稿。
- `404`：项目不存在。

业务要求：

- `uploaded` 只允许 `.txt` / `.md` 文件名。
- 后端使用 `rules/story-structure-extraction-rule.md` 构造模型调用。
- 后端必须执行去具体化校验。
- 后端必须基于抽取草稿计算 `outline_preview`，字段类型与 `ProjectStoryOutlinePayload` 一致。
- `outline_preview` 只用于前端预览和人工调整，不得在抽取接口中写入 `ProjectStoryOutline`。
- 校验失败时允许返回 `validation_status = "failed"` 的草稿，供前端展示失败原因，但该草稿不得应用。
- 响应不得返回完整 `source_text`。

错误提示：

- 请先上传或粘贴参考故事文本。
- 第一版只支持 txt 或 md 文本文件。
- 参考故事结构抽取暂不可用，请先配置并测试成功文本生成模型 API。
- 抽取结果未通过去具体化校验，不能应用到正式故事大纲。

### 4.7 查询参考框架草稿列表

```text
GET /api/projects/{project_id}/story-structure-drafts
```

响应：

- `200`：`ReferenceStoryStructureDraft[]`，按 `updated_at desc` 排序。
- `404`：项目不存在。

### 4.8 查询参考框架草稿详情

```text
GET /api/projects/{project_id}/story-structure-drafts/{draft_id}
```

响应：

- `200`：`ReferenceStoryStructureDraft`。
- `404`：项目或草稿不存在。

### 4.9 应用参考框架草稿

```text
POST /api/projects/{project_id}/story-structure-drafts/{draft_id}/apply
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| apply_mode | fill_empty / overwrite | 否 | 默认 `fill_empty` |
| user_requirements | string | 否 | 应用时补充要求 |

响应：

- `200`：更新后的 `ProjectStoryOutline`。
- `400`：草稿未通过校验、草稿已废弃、字段非法。
- `404`：项目或草稿不存在。

业务要求：

- 草稿必须属于当前项目。
- 草稿必须 `validation_status = "passed"`。
- `fill_empty` 只填充正式大纲为空的字段。
- `overwrite` 覆盖正式大纲相关字段。
- 成功后设置草稿 `status = "applied"`。
- 成功后标记下游内容为 `needs_review`。

### 4.10 废弃参考框架草稿

```text
POST /api/projects/{project_id}/story-structure-drafts/{draft_id}/discard
```

响应：

- `200`：废弃后的 `ReferenceStoryStructureDraft`。
- `404`：项目或草稿不存在。

业务要求：

- 设置草稿 `status = "discarded"`。
- 不影响正式故事大纲。
- 不标记下游内容。

## 5. 数据与迁移

需要新增或扩展：

- 扩展 `project_story_outlines`，新增故事背景、起点、结构、反转、情绪曲线、伏笔、节奏建议和容量建议等可空字段。
- 新增 `project_story_structure_drafts` 表，用于保存参考框架草稿、校验状态和应用状态。
- 新增索引：`project_id`、`status`、`validation_status`、`updated_at`。

迁移要求：

- 已有故事大纲数据必须保留。
- 新字段默认可空。
- 每个项目仍最多一条正式 `ProjectStoryOutline`。

## 6. 测试要求

- 测试正式故事大纲查询、保存和下游 `needs_review` 传播。
- 测试生成接口在 `preview` 模式下不写库、不标记下游。
- 测试生成接口在 `apply` 模式下写库并标记下游。
- 测试参考故事抽取强制使用结构抽取规则，不调用普通故事大纲规则。
- 使用包含《西游记》具体元素的输入测试去具体化校验，输出不得包含具体角色、地点、任务名称或经典桥段。
- 测试校验失败草稿不能应用到正式故事大纲。
- 测试仅生成参考框架草稿不标记下游内容。
- 测试 `fill_empty` 和 `overwrite` 两种应用模式。
- 测试文本模型未配置或未测试成功时返回明确错误。

## 7. 关联文档

- [故事大纲模块 PRD](../module-prds/story-outline.md)
- [项目工作台前端 Spec](../frontend-specs/project-workbench.md)
- [故事大纲前端 Spec](../frontend-specs/story-outline.md)
- [模型 API 配置后端 Spec](./model-api-settings.md)
- [参考故事结构抽取规则](../../../rules/story-structure-extraction-rule.md)
