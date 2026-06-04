# 后端接口 Spec：项目工作台

## 1. 适用范围

本文档定义项目工作台三类入口涉及的后端接口合同、数据对象和状态传播规则。

三类入口：

- 项目资料 / 资产：项目基础信息、项目世界观快照、项目角色快照。
- 故事文本：整体故事大纲、分集大纲、单集故事正文。
- 短剧制作：单集剧本、分镜镜头、字幕和发布文案。

覆盖能力：

- 查询和更新项目基础信息。
- 查询、保存故事文本相关产物。
- 查询、保存短剧制作相关产物。
- 根据上游变更标记下游内容为 `needs_review`。
- 确保短剧制作阶段沿用项目资料 / 资产和故事文本，不直接修改世界观或角色。

不覆盖能力：

- 世界观和角色快照的加载、微调和移除接口细节，见 [项目工作台资产快照接口](./project-workbench-assets.md)。
- 整体故事大纲 AI 生成、局部改写和参考故事结构抽取，见 [故事大纲](./story-outline.md)。
- 分集大纲与单集故事正文创作的详细字段和接口规则，见 [分集大纲与单集故事正文创作](./episode-outline.md)。
- 单集故事正文的 AI 创作、续写、润色、撤销润色、摘要、钩子提取和一致性质检；本阶段只要求前端展示入口，不新增后端 AI 接口。
- 世界观库、角色卡库原始资产 CRUD。
- AI 自动分镜拆解、分镜图生成、配音、字幕文件生成和视频生成。

## 2. 核心后端规则

### 2.1 工作台分区边界

后端不需要为三类入口单独创建新的路由前缀，但所有项目工作台接口必须遵守以下业务边界：

- 项目资料 / 资产是故事文本和短剧制作的公共上游。
- 故事文本是短剧制作的主要上游。
- 短剧制作接口只能读项目世界观、项目角色和故事文本作为上下文，不能修改项目世界观或项目角色。
- 如需修改世界观或角色，必须调用项目资料 / 资产相关接口。

### 2.2 状态定义

项目内创作产物使用 `ProjectArtifactStatus`：

- `draft`：草稿，内容尚未确认。
- `confirmed`：已确认，可作为后续内容基准。
- `needs_review`：上游内容发生变化，需要人工检查。

`needs_review` 只表示风险提示：

- 不删除原内容。
- 不自动覆盖原内容。
- 不自动重新生成内容。
- 用户重新检查并保存后，可以设为 `draft` 或 `confirmed`。

### 2.3 状态传播

后端在以下操作成功后，应标记下游已有内容为 `needs_review`：

| 上游操作 | 需要标记的下游内容 |
| --- | --- |
| 更新项目基础信息 | 整体故事大纲、分集大纲、单集故事正文、单集剧本、分镜、文案 |
| 加载、更新、移除项目世界观 | 整体故事大纲、分集大纲、单集故事正文、单集剧本、分镜、文案 |
| 加载、更新、移除项目角色 | 整体故事大纲、分集大纲、单集故事正文、单集剧本、分镜、文案 |
| 保存整体故事大纲 | 分集大纲、单集故事正文、单集剧本、分镜、文案 |
| 保存某集分集大纲 | 同集单集故事正文、同集单集剧本、同集分镜、同集文案 |
| 保存某集单集故事正文 | 同集单集剧本、同集分镜、同集文案 |
| 保存某集单集剧本 | 同集分镜、同集文案 |

### 2.4 集数校验

所有按集接口必须校验：

- `episode_no > 0`。
- `episode_no <= project.episode_count`。

不满足时返回 `400`，错误提示为：

- 集数编号必须在项目集数范围内。

### 2.5 短剧制作只读上游约束

短剧制作相关接口包括：

- 单集剧本。
- 分镜镜头。
- 字幕和发布文案。

这些接口不得更新：

- `ProjectWorldSnapshot`。
- `ProjectCharacterSnapshot`。
- `ProjectStoryOutline`。
- `ProjectEpisodeOutline`。
- `ProjectEpisodeContent`。

短剧制作接口可以读取上述内容作为上下文或返回摘要，但写入范围只能是短剧制作自己的数据对象。

## 3. 数据对象

### 3.1 ProjectStoryOutline

表示故事文本入口中的整体故事大纲。

字段以后端故事大纲 spec 为准：[故事大纲](./story-outline.md)。

### 3.2 ProjectEpisodeOutline

表示故事文本入口中的分集大纲。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 分集大纲 ID |
| project_id | string | 所属项目 ID |
| episode_no | number | 集数编号 |
| title | string | 单集标题 |
| synopsis | string | 单集梗概 |
| hook | string | 单集钩子 |
| conflict | string | 单集冲突 |
| reversal | string | 单集反转 |
| cliffhanger | string | 单集悬念 |
| duration_minutes | number | 预计时长 |
| status | draft / confirmed / needs_review | 内容状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.3 ProjectEpisodeContent

表示故事文本入口中的单集故事正文。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 单集故事正文 ID |
| project_id | string | 所属项目 ID |
| episode_no | number | 集数编号 |
| title | string | 章节标题 |
| detailed_content | string | 正文内容 |
| chapter_summary | string | 章节摘要 |
| hook | string | 本集钩子 |
| key_beats | string | 关键剧情节拍 |
| word_count | number | 正文字数统计 |
| previous_context_summary | string | 前文上下文引用 |
| quality_check_notes | string | 质检备注 |
| status | draft / confirmed / needs_review | 内容状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.4 ProjectEpisodeScript

表示短剧制作入口中的单集脚本。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 单集脚本 ID |
| project_id | string | 所属项目 ID |
| episode_no | number | 集数编号 |
| scene_text | string | 场景说明 |
| dialogue | string | 对白 |
| action_notes | string | 动作说明 |
| voiceover | string | 旁白 |
| status | draft / confirmed / needs_review | 内容状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.5 ProjectStoryboardShot

表示短剧制作入口中的分镜镜头。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 分镜镜头 ID |
| project_id | string | 所属项目 ID |
| episode_no | number | 集数编号 |
| shot_no | number | 镜头序号 |
| scene | string | 场景 |
| visual_prompt | string | 画面提示词 |
| camera | string | 镜头 / 机位 |
| duration_seconds | number | 镜头时长 |
| dialogue_or_voiceover | string | 对白或旁白 |
| status | draft / confirmed / needs_review | 内容状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.6 ProjectCopywriting

表示短剧制作入口中的字幕和发布文案。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 文案 ID |
| project_id | string | 所属项目 ID |
| episode_no | number | 集数编号 |
| subtitles | string | 字幕 |
| platform_title | string | 平台标题 |
| platform_description | string | 平台简介 |
| publish_copy | string | 发布文案 |
| status | draft / confirmed / needs_review | 内容状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

## 4. 接口定义

### 4.1 查询项目详情

```text
GET /api/projects/{project_id}
```

响应：

- `200`：`Project`。
- `404`：项目不存在。

### 4.2 更新项目基础信息

```text
PUT /api/projects/{project_id}
```

请求体：项目基础信息字段。

业务要求：

- 必须继续校验创意、集数、单集时长和总时长。
- 保存成功后，故事文本和短剧制作已有内容标记为 `needs_review`。

### 4.3 查询整体故事大纲

```text
GET /api/projects/{project_id}/story-outline
```

响应：

- `200`：`ProjectStoryOutline | null`。
- `404`：项目不存在。

### 4.4 保存整体故事大纲

```text
PUT /api/projects/{project_id}/story-outline
```

请求体：`ProjectStoryOutlinePayload`。

业务要求：

- 创建或更新正式整体故事大纲。
- 保存成功后，分集大纲、单集故事正文、单集剧本、分镜和文案标记为 `needs_review`。

### 4.5 查询分集大纲列表

```text
GET /api/projects/{project_id}/episode-outlines
```

响应：

- `200`：`ProjectEpisodeOutline[]`，按 `episode_no asc` 排序。
- `404`：项目不存在。

### 4.6 保存某集分集大纲

```text
PUT /api/projects/{project_id}/episode-outlines/{episode_no}
```

请求体：`ProjectEpisodeOutlinePayload`。

业务要求：

- 校验 `episode_no` 在项目集数范围内。
- 创建或更新对应集分集大纲。
- 保存成功后，同集单集故事正文、单集剧本、分镜和文案标记为 `needs_review`。

### 4.7 查询某集单集故事正文

```text
GET /api/projects/{project_id}/episode-contents/{episode_no}
```

响应：

- `200`：`ProjectEpisodeContent | null`。
- `400`：集数编号非法。
- `404`：项目不存在。

### 4.8 保存某集单集故事正文

```text
PUT /api/projects/{project_id}/episode-contents/{episode_no}
```

请求体：`ProjectEpisodeContentPayload`。

业务要求：

- 校验 `episode_no` 在项目集数范围内。
- 创建或更新对应集单集故事正文。
- 保存成功后，同集单集剧本、分镜和文案标记为 `needs_review`。

### 4.9 查询某集剧本

```text
GET /api/projects/{project_id}/episode-scripts/{episode_no}
```

响应：

- `200`：`ProjectEpisodeScript | null`。
- `400`：集数编号非法。
- `404`：项目不存在。

### 4.10 保存某集剧本

```text
PUT /api/projects/{project_id}/episode-scripts/{episode_no}
```

请求体：`ProjectEpisodeScriptPayload`。

业务要求：

- 校验 `episode_no` 在项目集数范围内。
- 创建或更新对应集剧本。
- 不得修改世界观、角色、整体故事大纲、分集大纲或单集故事正文。
- 保存成功后，同集分镜和文案标记为 `needs_review`。

### 4.11 查询某集分镜镜头

```text
GET /api/projects/{project_id}/storyboard-shots/{episode_no}
```

响应：

- `200`：`ProjectStoryboardShot[]`，按 `shot_no asc` 排序。
- `400`：集数编号非法。
- `404`：项目不存在。

### 4.12 新增某集分镜镜头

```text
POST /api/projects/{project_id}/storyboard-shots/{episode_no}
```

请求体：`ProjectStoryboardShotPayload`。

业务要求：

- 校验 `episode_no` 在项目集数范围内。
- 只写入分镜镜头，不修改故事文本和资产快照。

### 4.13 更新某集分镜镜头

```text
PUT /api/projects/{project_id}/storyboard-shots/{episode_no}/{shot_id}
```

请求体：`ProjectStoryboardShotPayload`。

业务要求：

- 分镜必须属于当前项目和当前集。
- 只更新分镜镜头，不修改故事文本和资产快照。

### 4.14 删除某集分镜镜头

```text
DELETE /api/projects/{project_id}/storyboard-shots/{episode_no}/{shot_id}
```

业务要求：

- 分镜必须属于当前项目和当前集。
- 删除分镜不影响故事文本和资产快照。

### 4.15 查询某集字幕和发布文案

```text
GET /api/projects/{project_id}/copywriting/{episode_no}
```

响应：

- `200`：`ProjectCopywriting | null`。
- `400`：集数编号非法。
- `404`：项目不存在。

### 4.16 保存某集字幕和发布文案

```text
PUT /api/projects/{project_id}/copywriting/{episode_no}
```

请求体：`ProjectCopywritingPayload`。

业务要求：

- 校验 `episode_no` 在项目集数范围内。
- 只写入文案，不修改故事文本和资产快照。

## 5. 错误提示

| 场景 | 错误提示 |
| --- | --- |
| 项目不存在 | 项目不存在 |
| 集数编号非法 | 集数编号必须在项目集数范围内 |
| 分镜不存在 | 项目分镜不存在 |
| 保存失败 | 保存失败，请稍后重试 |

## 6. 验收标准

- 项目详情可以读取。
- 项目基础信息可以保存，并触发故事文本和短剧制作内容 `needs_review`。
- 整体故事大纲可以读取和保存。
- 分集大纲可以按集保存，且只影响对应集下游内容状态。
- 单集故事正文可以按集保存，且只影响对应集短剧制作内容状态。
- 单集剧本可以按集保存，且不修改世界观、角色、整体故事大纲、分集大纲或单集故事正文。
- 分镜镜头可以按集新增、更新、删除。
- 字幕和发布文案可以按集保存。
- 所有按集接口必须拒绝超出项目集数范围的 `episode_no`。
- 短剧制作接口不得写入项目世界观快照和项目角色快照。

## 7. 关联文档

- [第一期 PRD](../prd.md)
- [项目工作台模块 PRD](../module-prds/project-workbench.md)
- [项目工作台前端 Spec](../frontend-specs/project-workbench.md)
- [分集大纲与单集故事正文创作后端 Spec](./episode-outline.md)
- [项目工作台资产快照后端 Spec](./project-workbench-assets.md)
- [故事大纲后端 Spec](./story-outline.md)
