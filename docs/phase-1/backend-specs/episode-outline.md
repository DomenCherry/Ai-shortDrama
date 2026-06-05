# 后端接口 Spec：分集大纲与单集故事正文创作

## 1. 适用范围

本文档定义故事文本入口下“分集大纲与单集故事正文创作”的后端接口合同、数据对象、校验规则和状态传播规则。

覆盖能力：

- 查询分集大纲列表。
- 保存某一集分集大纲。
- 查询某一集单集故事正文。
- 保存某一集单集故事正文。
- 保存分集大纲后，标记同集单集故事正文和短剧制作下游为 `needs_review`。
- 保存单集故事正文后，标记同集单集剧本、分镜和文案为 `needs_review`。

不覆盖能力：

- 自动生成完整分集大纲。
- 单集故事正文 AI 创作。
- 续写。
- 润色。
- 撤销润色。
- 自动摘要。
- 钩子提取。
- 一致性质检。
- 独立角色参考、设定参考、文风或灵感后端接口。

上述 AI 创作能力本阶段只要求前端展示按钮或面板入口，不新增后端路由、schema、service 或模型调用。

## 2. 核心后端规则

### 2.1 模块边界

- 分集大纲和单集故事正文归属于“故事文本”。
- 单集故事正文是“短剧制作”的主要输入。
- 单集故事正文不是单集剧本。
- 短剧制作接口不得更新分集大纲和单集故事正文。
- 项目世界观和项目角色快照由项目资料 / 资产接口维护，本模块只读取其结果，不写入。

### 2.2 集数校验

所有按集接口必须校验：

- `episode_no > 0`。
- `episode_no <= project.episode_count`。

不满足时返回 `400`：

- 集数编号必须在项目集数范围内。

### 2.3 状态定义

分集大纲和单集故事正文使用 `ProjectArtifactStatus`：

- `draft`：草稿，内容尚未确认。
- `confirmed`：已确认，可作为后续内容基准。
- `needs_review`：上游内容发生变化，需要人工检查。

`needs_review` 不删除、不覆盖、不自动重新生成内容。

### 2.4 状态传播

| 上游操作 | 需要标记的下游内容 |
| --- | --- |
| 保存整体故事大纲 | 分集大纲、单集故事正文、单集剧本、分镜、文案 |
| 保存某集分集大纲 | 同集单集故事正文、同集单集剧本、同集分镜、同集文案 |
| 保存某集单集故事正文 | 同集单集剧本、同集分镜、同集文案 |

状态传播只影响已存在的下游内容。不存在的下游内容不需要创建占位记录。

### 2.5 字数统计

`word_count` 可由后端根据 `detailed_content` 计算，也可接收前端传入后重新计算覆盖。推荐以后端计算为准，避免前端统计差异。

如果 `detailed_content` 为空，`word_count = 0`。

### 2.6 AI 能力占位规则

本阶段不得新增以下接口：

- `POST /api/projects/{project_id}/episode-contents/{episode_no}/generate`
- `POST /api/projects/{project_id}/episode-contents/{episode_no}/continue`
- `POST /api/projects/{project_id}/episode-contents/{episode_no}/polish`
- `POST /api/projects/{project_id}/episode-contents/{episode_no}/undo-polish`
- `POST /api/projects/{project_id}/episode-contents/{episode_no}/summarize`
- `POST /api/projects/{project_id}/episode-contents/{episode_no}/extract-hook`
- `POST /api/projects/{project_id}/episode-contents/{episode_no}/quality-check`

前端点击相关按钮时，只展示“该 AI 能力暂未接入，后续完善”，不发送请求。

## 3. 数据对象

### 3.1 ProjectEpisodeOutline

表示单集大纲。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 分集大纲 ID |
| project_id | string | 所属项目 ID |
| episode_no | number | 集数编号 |
| title | string | 本集标题 |
| synopsis | string | 单集梗概 |
| hook | string | 开头钩子 |
| conflict | string | 主要冲突 |
| reversal | string | 关键反转 |
| cliffhanger | string | 结尾悬念 |
| duration_minutes | number | 预计时长 |
| status | draft / confirmed / needs_review | 内容状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.2 ProjectEpisodeOutlinePayload

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| title | string | 否 | 本集标题 |
| synopsis | string | 否 | 单集梗概 |
| hook | string | 否 | 开头钩子 |
| conflict | string | 否 | 主要冲突 |
| reversal | string | 否 | 关键反转 |
| cliffhanger | string | 否 | 结尾悬念 |
| duration_minutes | number | 否 | 预计时长 |
| status | draft / confirmed / needs_review | 否 | 内容状态，默认 `draft` |

### 3.3 ProjectEpisodeContent

表示单集故事正文。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 单集故事正文 ID |
| project_id | string | 所属项目 ID |
| episode_no | number | 集数编号 |
| title | string | 兼容镜像字段，取当前集分集大纲标题；不作为单集故事正文的独立标题来源 |
| detailed_content | string | 正文内容 |
| chapter_summary | string | 正文摘要，正文完成后的成稿摘要 |
| hook | string | 正文钩子 / 传播点，从正文中沉淀的吸引点、悬念或传播点 |
| key_beats | string | 正文节拍，正文实际展开后的关键剧情节点 |
| word_count | number | 正文字数统计 |
| previous_context_summary | string | 前文参考，例如前几集正文摘要、上集结尾和未回收伏笔 |
| quality_check_notes | string | 质检备注 |
| status | draft / confirmed / needs_review | 内容状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.4 ProjectEpisodeContentPayload

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| title | string | 否 | 兼容镜像字段，应由服务端或调用方使用当前集分集大纲标题填充；正文页不单独编辑 |
| detailed_content | string | 否 | 正文内容 |
| chapter_summary | string | 否 | 正文摘要，正文完成后的成稿摘要 |
| hook | string | 否 | 正文钩子 / 传播点 |
| key_beats | string | 否 | 正文节拍 |
| previous_context_summary | string | 否 | 前文参考 |
| quality_check_notes | string | 否 | 质检备注 |
| status | draft / confirmed / needs_review | 否 | 内容状态，默认 `draft` |

兼容要求：

- 当前实现如仅包含 `detailed_content`、`key_beats` 和 `status`，新增字段应允许为空。
- 字段扩展不得破坏已有项目数据读取和保存。
- 单集故事正文标题与分集大纲标题语义一致。后续如收敛数据模型，应优先保留 `ProjectEpisodeOutline.title`，`ProjectEpisodeContent.title` 可作为兼容镜像字段迁移或废弃。

## 4. 接口定义

### 4.1 查询分集大纲列表

```text
GET /api/projects/{project_id}/episode-outlines
```

响应：

- `200`：`ProjectEpisodeOutline[]`，按 `episode_no asc` 排序。
- `404`：项目不存在。

业务要求：

- 如果某些集尚未保存分集大纲，可返回已存在记录；前端根据项目集数补齐空表单。
- 不在查询时自动创建缺失分集大纲。

### 4.2 保存某集分集大纲

```text
PUT /api/projects/{project_id}/episode-outlines/{episode_no}
```

请求体：`ProjectEpisodeOutlinePayload`。

响应：

- `200`：保存后的 `ProjectEpisodeOutline`。
- `400`：集数编号非法、字段非法或状态非法。
- `404`：项目不存在。

业务要求：

- 校验 `episode_no` 在项目集数范围内。
- 创建或更新对应集分集大纲。
- 空字符串统一保存为 `null` 或空字符串，需与现有项目工作台接口保持一致。
- `status` 只允许 `draft`、`confirmed`、`needs_review`。
- 保存成功后，标记同集单集故事正文、单集剧本、分镜和文案为 `needs_review`。

### 4.3 查询某集单集故事正文

```text
GET /api/projects/{project_id}/episode-contents/{episode_no}
```

响应：

- `200`：`ProjectEpisodeContent | null`。
- `400`：集数编号非法。
- `404`：项目不存在。

业务要求：

- 不存在时返回 `null`。
- 不在查询时自动创建空正文记录。

### 4.4 保存某集单集故事正文

```text
PUT /api/projects/{project_id}/episode-contents/{episode_no}
```

请求体：`ProjectEpisodeContentPayload`。

响应：

- `200`：保存后的 `ProjectEpisodeContent`。
- `400`：集数编号非法、字段非法或状态非法。
- `404`：项目不存在。

业务要求：

- 校验 `episode_no` 在项目集数范围内。
- 创建或更新对应集单集故事正文。
- `word_count` 由后端根据 `detailed_content` 计算。
- `status` 只允许 `draft`、`confirmed`、`needs_review`。
- 保存成功后，标记同集单集剧本、分镜和文案为 `needs_review`。
- 保存单集故事正文不得修改项目世界观、项目角色、整体故事大纲、分集大纲、单集剧本、分镜或文案内容。

## 5. 前端参考面板数据来源

本阶段不新增独立参考面板接口。前端参考面板可以组合读取以下现有接口：

- 项目详情：`GET /api/projects/{project_id}`。
- 项目世界观快照：`GET /api/projects/{project_id}/world-snapshots`。
- 项目角色快照：`GET /api/projects/{project_id}/character-snapshots`。
- 整体故事大纲：`GET /api/projects/{project_id}/story-outline`。
- 分集大纲列表：`GET /api/projects/{project_id}/episode-outlines`。
- 单集故事正文：`GET /api/projects/{project_id}/episode-contents/{episode_no}`。

角色参考、设定参考、文风和灵感面板在本阶段只要求前端展示入口。若无可读取数据，前端展示空状态或“暂未接入”提示。

## 6. 错误提示

| 场景 | 错误提示 |
| --- | --- |
| 项目不存在 | 项目不存在 |
| 集数编号非法 | 集数编号必须在项目集数范围内 |
| 状态非法 | 内容状态非法 |
| 分集大纲保存失败 | 分集大纲保存失败，请稍后重试 |
| 单集故事正文保存失败 | 单集故事正文保存失败，请稍后重试 |

## 7. 验收标准

- 分集大纲列表可以读取。
- 分集大纲可以按集保存。
- 单集故事正文可以按集读取和保存。
- 保存分集大纲后，同集单集故事正文、剧本、分镜和文案标记为 `needs_review`。
- 保存单集故事正文后，同集剧本、分镜和文案标记为 `needs_review`。
- 所有按集接口拒绝超出项目集数范围的 `episode_no`。
- 保存单集故事正文不会修改世界观、角色、整体故事大纲、分集大纲、剧本、分镜或文案内容。
- 本阶段不新增任何单集故事正文 AI 生成、续写、润色、摘要、钩子提取或质检接口。

## 8. 关联文档

- [第一期 PRD](../prd.md)
- [分集大纲与单集故事正文创作模块 PRD](../module-prds/episode-outline.md)
- [项目工作台模块 PRD](../module-prds/project-workbench.md)
- [分集大纲与单集故事正文创作前端 Spec](../frontend-specs/episode-outline.md)
- [项目工作台后端 Spec](./project-workbench.md)
