# 项目工作台页面 Spec

## 1. 页面目标

- 页面路径：`/projects/[id]`
- 目标：把项目工作台从线性阶段导航调整为三类工作入口：项目资料 / 资产、故事文本、短剧制作。
- 当前阶段不做完整 AI 生成闭环，先搭建可保存、可检查、可继续迭代的项目内创作结构。

三类入口定义：

- 项目资料 / 资产：维护基础信息、世界观和角色，作为整个项目的公共上下文。
- 故事文本：负责把项目写成完整故事，包含整体故事大纲、分集大纲和每集具体故事内容，目标是形成可读的故事 / 小说化文本。
- 短剧制作：负责把每集具体故事内容转成视频生产所需文本，包括单集脚本、分镜、字幕和平台发布文案。

## 2. 信息架构

### 2.1 顶部项目概览

展示：

- 项目名称。
- 项目状态。
- 题材。
- 平台。
- 集数。
- 单集时长。
- 总时长。
- 创意描述。
- 更新时间。

操作：

- 返回项目管理。
- 保存项目基础信息。

### 2.2 工作入口

进入项目工作台后，主区域首先展示三个入口：

- 项目资料 / 资产。
- 故事文本。
- 短剧制作。

入口应展示简短状态摘要：

- 项目资料 / 资产：是否已加载世界观、已加载角色数量、项目基础信息是否完整。
- 故事文本：整体故事大纲状态、分集大纲完成数量、单集内容完成数量。
- 短剧制作：当前选中集的剧本状态、分镜数量、文案状态。

### 2.3 项目资料 / 资产

包含：

- 基础信息。
- 世界观与角色。

基础信息字段：

- 标题。
- 创意描述。
- 目标平台。
- 题材。
- 集数。
- 单集时长。
- 目标受众。
- 风格。
- 备注。

世界观与角色能力：

- 展示已加载项目世界观快照。
- 展示已加载项目角色快照。
- 从世界观库加载 active 世界观。
- 从角色卡库加载 active 角色卡。
- 编辑项目内世界观快照。
- 编辑项目内角色快照。
- 从项目中移除世界观或角色快照。

### 2.4 故事文本

包含：

- 整体故事大纲。
- 分集大纲。
- 单集内容。

整体故事大纲：

- 展示正式故事大纲字段。
- 支持手动编辑和保存。
- 提供【AI提取】入口，跳转到 `/projects/{project_id}/story-outline/extract`。
- 参考故事结构抽取的详细交互见 [项目故事大纲 Spec](./story-outline.md)。

分集大纲：

- 按项目集数展示分集列表。
- 支持选择某一集编辑标题、梗概、钩子、冲突、反转、悬念、预计时长和状态。

单集内容：

- 按集维护详细剧情内容。
- 按集维护关键剧情节拍。
- 单集内容是短剧制作的主要输入。

### 2.5 短剧制作

包含：

- 单集剧本。
- 分镜。
- 字幕 / 发布文案。

单集剧本：

- 按集维护场景说明。
- 按集维护对白。
- 按集维护动作说明。
- 按集维护旁白。

分镜：

- 按集维护镜头列表。
- 每个镜头包含镜头序号、场景、画面提示词、镜头 / 机位、镜头时长、对白或旁白。

字幕 / 发布文案：

- 按集维护字幕。
- 平台标题。
- 平台简介。
- 发布文案。

短剧制作约束：

- 短剧制作区域不能直接编辑项目世界观和项目角色。
- 短剧制作区域应展示当前沿用的世界观、角色和故事文本摘要，作为只读上下文。
- 如果用户需要修改世界观、角色、整体故事大纲、分集大纲或单集内容，应回到项目资料 / 资产或故事文本入口修改。

## 3. 交互规则

- 工作台加载失败时显示中文错误，并保留返回项目管理入口。
- 三类入口之间切换不应丢失已保存内容。
- 保存项目设定时继续执行创意、集数、单集时长和总时长校验。
- 状态支持 `draft`、`confirmed`、`needs_review`，前端展示为"草稿""已确认""需要检查"。
- `needs_review` 表示内容仍保留，但因上游变化可能不再一致，需要用户重新检查。
- 前端成功提示应覆盖真实影响范围，不能只提示部分下游内容。
- 删除项目内快照只影响项目副本，不影响世界观库或角色卡库原始资产。
- 保存项目内快照微调内容只更新当前项目副本，不影响世界观库或角色卡库原始资产。

### 3.1 状态传播提示

- 修改项目设定后，故事文本和短剧制作已有内容标记为 `needs_review`。
- 加载、更新或移除项目世界观后，故事文本和短剧制作已有内容标记为 `needs_review`。
- 加载、更新或移除项目角色后，故事文本和短剧制作已有内容标记为 `needs_review`。
- 保存整体故事大纲后，分集大纲、单集内容、剧本、分镜和文案标记为 `needs_review`。
- 保存分集大纲后，同集单集内容、剧本、分镜和文案标记为 `needs_review`。
- 保存单集内容后，同集剧本、分镜和文案标记为 `needs_review`。
- 保存剧本后，同集分镜和文案标记为 `needs_review`。

### 3.2 内联加载资产规则

- 用户可在"项目资料 / 资产"入口内直接打开资产选择面板，从已有世界观库和角色卡库中选择资产并加载到当前项目，无需跳转到资产库页面。
- 资产选择面板应分别列出世界观库中状态为 `active` 的世界观和角色卡库中状态为 `active` 的角色卡。
- 项目世界观只能加载一个；当项目已有世界观时，世界观选择面板应展示当前世界观已存在，并禁用继续加载第二个世界观。
- 项目角色可以加载多个；同一角色卡已加载到当前项目时，应标记为"已加载"且不可重复选择。
- 未加载的 active 角色卡仍可继续加载到项目。
- 加载操作创建项目内快照副本，加载成功后自动刷新快照列表。
- 加载世界观或角色卡后，故事文本和短剧制作内容应标记为 `needs_review`。
- 资产选择面板提供"前往资产库管理"入口，方便用户新建或编辑资产，但常规加载流程不要求离开工作台。

### 3.3 项目世界观微调规则

- 世界观卡片展示来源世界观名称、来源版本、加载时间、更新时间和当前项目内摘要。
- 世界观卡片提供"编辑项目世界观"入口，打开项目内世界观编辑区。
- 编辑区应允许用户调整项目内世界观名称、题材、基础设定快照和条目快照内容。
- 编辑区必须提示"此处只修改当前项目世界观，不会修改世界观库原始内容"。
- 保存成功后刷新项目世界观快照，并展示故事文本和短剧制作内容需要检查的提示。
- 取消编辑时，如果有未保存内容，应提示确认。

### 3.4 项目角色微调规则

- 角色卡片展示角色名、性别、人物原型、来源角色卡版本、加载时间、更新时间、视觉描述和参考图状态。
- 角色卡片提供"编辑项目角色"入口，打开项目内角色编辑区。
- 编辑区应允许用户调整项目内角色名称、人物原型、人物目标、人物关系、冲突点、反转秘密、情感弧线、剧情功能、口吻补充和视觉描述。
- 编辑区必须提示"此处只修改当前项目角色，不会修改角色卡库原始内容"。
- 保存成功后刷新项目角色快照，并展示故事文本和短剧制作内容需要检查的提示。
- 取消编辑时，如果有未保存内容，应提示确认。

### 3.5 短剧制作只读上游上下文

- 短剧制作区域应展示当前集使用的只读上下文摘要。
- 摘要至少包括：世界观名称、角色数量、整体故事大纲状态、当前集分集大纲状态、当前集单集内容状态。
- 短剧制作区域不得出现世界观或角色编辑表单。
- 可以提供"返回项目资料 / 资产"或"返回故事文本"的跳转入口。
- 如果上游内容为 `needs_review`，短剧制作区域应提示用户先检查上游内容。

## 4. API 依赖

项目工作台内容接口应与 [项目工作台后端 Spec](../backend-specs/project-workbench.md) 保持一致。项目世界观和项目角色快照接口应与 [项目工作台资产快照后端 Spec](../backend-specs/project-workbench-assets.md) 保持一致。故事大纲保存和参考故事结构抽取接口应与 [故事大纲后端 Spec](../backend-specs/story-outline.md) 保持一致。

| 行为 | 前端方法 | 后端接口 | 请求数据 | 响应数据 | 错误处理 |
| --- | --- | --- | --- | --- | --- |
| 读取/更新项目 | `getProject` / `updateProject` | `GET/PUT /api/projects/{project_id}` | 项目基础字段 | 项目详情 | 展示项目加载或保存失败 |
| 读取世界观快照 | `listProjectWorldSnapshots` | `GET /api/projects/{project_id}/world-snapshots` | project_id | `ProjectWorldSnapshot[]`，第一版最多 1 条 | 展示世界观快照加载失败 |
| 加载世界观到项目 | `loadWorldBookToProject` | `POST /api/projects/{project_id}/world-snapshots` | `source_world_book_id`、`load_mode`、`replace_snapshot_id` | 项目世界观快照 | 目标项目已有世界观时展示单世界观限制提示 |
| 更新项目世界观快照 | `updateProjectWorldSnapshot` | `PUT /api/projects/{project_id}/world-snapshots/{snapshot_id}` | 世界观快照字段 | 更新后的项目世界观快照 | 展示保存失败，保留用户输入 |
| 移除世界观快照 | `deleteProjectWorldSnapshot` | `DELETE /api/projects/{project_id}/world-snapshots/{snapshot_id}` | project_id、snapshot_id | `{ ok: true }` | 展示世界观移除失败 |
| 读取角色快照 | `listProjectCharacterSnapshots` | `GET /api/projects/{project_id}/character-snapshots` | project_id | `ProjectCharacterSnapshot[]` | 展示角色快照加载失败 |
| 加载角色卡到项目 | `loadCharacterCardToProject` | `POST /api/projects/{project_id}/character-snapshots` | `source_character_card_id`、`load_mode`、`replace_snapshot_id` | 项目角色快照 | 同一角色卡已加载时展示不可重复加载提示 |
| 更新项目角色快照 | `updateProjectCharacterSnapshot` | `PUT /api/projects/{project_id}/character-snapshots/{snapshot_id}` | 角色快照字段 | 更新后的项目角色快照 | 展示保存失败，保留用户输入 |
| 移除角色快照 | `deleteProjectCharacterSnapshot` | `DELETE /api/projects/{project_id}/character-snapshots/{snapshot_id}` | project_id、snapshot_id | `{ ok: true }` | 展示角色移除失败 |
| 列出可用世界观 | `listWorldBooks` | `GET /api/world-books` | `status=active` | active 世界观列表 | 展示可用世界观加载失败 |
| 列出可用角色卡 | `listCharacterCards` | `GET /api/character-cards` | `status=active` | active 角色卡列表 | 展示可用角色卡加载失败 |
| 读取/保存整体大纲 | `getProjectStoryOutline` / `updateProjectStoryOutline` | `GET/PUT /api/projects/{project_id}/story-outline` | 整体大纲字段 | 整体大纲 | 展示大纲加载或保存失败 |
| 读取/保存分集大纲 | `listProjectEpisodeOutlines` / `updateProjectEpisodeOutline` | `GET /api/projects/{project_id}/episode-outlines`，`PUT /api/projects/{project_id}/episode-outlines/{episode_no}` | 分集大纲字段 | 分集大纲 | 展示分集大纲加载或保存失败 |
| 读取/保存单集内容 | `getProjectEpisodeContent` / `updateProjectEpisodeContent` | `GET/PUT /api/projects/{project_id}/episode-contents/{episode_no}` | 单集内容字段 | 单集内容 | 展示单集内容加载或保存失败 |
| 读取/保存剧本 | `getProjectEpisodeScript` / `updateProjectEpisodeScript` | `GET/PUT /api/projects/{project_id}/episode-scripts/{episode_no}` | 剧本字段 | 剧本 | 展示剧本加载或保存失败 |
| 分镜镜头列表 | `listProjectStoryboardShots` | `GET /api/projects/{project_id}/storyboard-shots/{episode_no}` | episode_no | 分镜镜头列表 | 展示分镜加载失败 |
| 新增分镜镜头 | `createProjectStoryboardShot` | `POST /api/projects/{project_id}/storyboard-shots/{episode_no}` | 镜头字段 | 分镜镜头 | 展示分镜新增失败 |
| 更新分镜镜头 | `updateProjectStoryboardShot` | `PUT /api/projects/{project_id}/storyboard-shots/{episode_no}/{shot_id}` | 镜头字段 | 分镜镜头 | 展示分镜保存失败 |
| 删除分镜镜头 | `deleteProjectStoryboardShot` | `DELETE /api/projects/{project_id}/storyboard-shots/{episode_no}/{shot_id}` | shot_id | `{ ok: true }` | 展示分镜删除失败 |
| 读取/保存文案 | `getProjectCopywriting` / `updateProjectCopywriting` | `GET/PUT /api/projects/{project_id}/copywriting/{episode_no}` | 文案字段 | 文案 | 展示文案加载或保存失败 |

## 5. 响应式要求

- 三个工作入口在桌面端可横向并列，在窄屏下改为单列。
- 入口卡片高度应稳定，状态文案过长时自然换行。
- 分集选择器、剧本、分镜、文案表单在窄屏下不横向溢出。
- 短剧制作的只读上下文摘要不应遮挡编辑表单。

## 6. 验收标准

- 项目列表可进入 `/projects/[id]`，创建项目成功后直接进入工作台。
- 工作台主区域清晰展示项目资料 / 资产、故事文本、短剧制作三个入口。
- 项目资料 / 资产入口可以维护基础信息、世界观和角色。
- 故事文本入口可以维护整体故事大纲、分集大纲和单集内容。
- 短剧制作入口可以维护剧本、分镜和文案。
- 短剧制作入口不能直接编辑世界观和角色。
- 短剧制作入口展示当前沿用的世界观、角色和故事文本摘要。
- 基础信息保存、校验、时长影响提示正常。
- 可在项目资料 / 资产入口内直接打开资产选择面板，选择并加载世界观或角色卡到项目。
- 每个项目最多只能加载一个世界观；已有世界观时，世界观继续加载入口禁用或展示明确阻止提示。
- 项目可以加载多个角色；同一角色卡已加载时，在资产选择面板中显示为"已加载"且不可重复选择。
- 用户可以编辑并保存项目世界观快照，刷新后微调内容仍存在。
- 用户可以编辑并保存项目角色快照，刷新后微调内容仍存在。
- 保存项目世界观或项目角色微调内容不会修改世界观库或角色卡库原始内容。
- 加载或保存项目资产后，故事文本和短剧制作已有内容标记为"需要检查"。
- 保存整体故事大纲、分集大纲、单集内容或剧本后，下游对应内容显示"需要检查"。
- `npm --prefix apps/web run typecheck` 通过。

## 7. 非目标

- 不在短剧制作区域提供世界观或角色编辑能力。
- 不接完整 AI 生成闭环。
- 不做项目内快照与来源资产的复杂差异对比。
- 不做资产库新版本自动同步到项目快照。
- 不做完整视频生成和素材导出。
