# 项目工作台页面 Spec

## 1. 页面目标

- 页面路径：`/projects/[id]`
- 目标：把项目从基础资料管理升级为短剧创作工作台，承接“项目设定 -> 世界观与角色 -> 故事大纲 -> 分集大纲 -> 单集内容 -> 剧本 -> 分镜与文案”的完整人工编辑流程。
- 当前阶段不做 AI 生成，只搭建可保存、可检查、可继续迭代的项目内创作结构。

## 2. 信息架构

- 项目概览：项目名称、状态、题材、平台、集数、单集时长、总时长、创意描述、更新时间。
- 阶段导航：基础信息、世界观与角色、故事大纲、分集大纲、单集内容、剧本、分镜与文案。
- 基础信息：复用项目创建字段，支持保存和还原。
- 世界观与角色：展示已加载项目快照，支持从资产库直接选择并加载世界观和角色卡到项目，支持项目内微调和从项目移除。每个项目最多一个世界观；角色可以多个，但同一角色卡不能重复加载。
- 故事大纲：正式大纲编辑、AI 生成、局部改写、参考故事结构抽取和参考框架应用。详细字段与交互见 [项目故事大纲 Spec](./story-outline.md)。
- 分集大纲：按项目集数展示分集表，单集编辑标题、梗概、钩子、冲突、反转、悬念、预计时长、状态。
- 单集内容：按集维护详细剧情内容和关键剧情节拍。
- 剧本：按集维护场景说明、对白、动作说明和旁白。
- 分镜与文案：按集维护镜头列表、字幕、平台标题、平台简介、发布文案。

## 3. 交互规则

- 工作台加载失败时显示中文错误，并保留返回项目管理入口。
- 保存项目设定时继续执行创意、集数、单集时长和总时长校验。
- 修改项目设定、移除项目世界观或角色后，下游创作内容标记为 `needs_review`。
- 保存项目世界观或项目角色微调内容后，下游创作内容标记为 `needs_review`。
- 保存整体故事大纲后，分集大纲、单集内容、剧本、分镜和文案标记为 `needs_review`。
- 保存分集大纲后，同集单集内容、剧本、分镜和文案标记为 `needs_review`。
- 保存单集内容后，同集剧本、分镜和文案标记为 `needs_review`。
- 保存剧本后，同集分镜和文案标记为 `needs_review`。
- 前端成功提示应覆盖真实影响范围，不能只提示部分下游内容。
- 状态支持 `draft`、`confirmed`、`needs_review`，前端展示为"草稿""已确认""需要检查"。
- 删除项目内快照只影响项目副本，不影响世界观库或角色卡库原始资产。
- 保存项目内快照微调内容只更新当前项目副本，不影响世界观库或角色卡库原始资产。

### 3.1 内联加载资产规则

- 用户可在"世界观与角色"tab 内直接打开资产选择面板，从已有世界观库和角色卡库中选择资产并加载到当前项目，无需跳转到资产库页面。
- 资产选择面板应分别列出世界观库中状态为 `active` 的世界观和角色卡库中状态为 `active` 的角色卡。
- 项目世界观只能加载一个；当项目已有世界观时，世界观选择面板应展示当前世界观已存在，并禁用继续加载第二个世界观。
- 项目角色可以加载多个；同一角色卡已加载到当前项目时，应标记为"已加载"且不可重复选择。
- 未加载的 active 角色卡仍可继续加载到项目。
- 加载操作创建项目内快照副本，加载成功后自动刷新快照列表。
- 新增加载世界观或角色卡后，下游创作内容（故事大纲、分集大纲等）应标记为 `needs_review`。
- 资产选择面板提供"前往资产库管理"入口，方便用户新建或编辑资产，但常规加载流程不要求离开工作台。

### 3.2 项目世界观微调规则

- 世界观卡片展示来源世界观名称、来源版本、加载时间、更新时间和当前项目内摘要。
- 世界观卡片提供"编辑项目世界观"入口，打开项目内世界观编辑区。
- 编辑区应允许用户调整项目内世界观名称、题材、基础设定快照和条目快照内容。
- 编辑区必须提示"此处只修改当前项目世界观，不会修改世界观库原始内容"。
- 保存成功后刷新项目世界观快照，并展示下游内容需要检查的提示。
- 取消编辑时，如果有未保存内容，应提示确认。

### 3.3 项目角色微调规则

- 角色卡片展示角色名、性别、人物原型、来源角色卡版本、加载时间、更新时间、视觉描述和参考图状态。
- 角色卡片提供"编辑项目角色"入口，打开项目内角色编辑区。
- 编辑区应允许用户调整项目内角色名称、人物原型、人物目标、人物关系、冲突点、反转秘密、情感弧线、剧情功能、口吻补充和视觉描述。
- 编辑区必须提示"此处只修改当前项目角色，不会修改角色卡库原始内容"。
- 保存成功后刷新项目角色快照，并展示下游内容需要检查的提示。
- 取消编辑时，如果有未保存内容，应提示确认。

## 4. API 依赖

项目世界观和项目角色快照接口应与 [项目工作台资产快照后端 Spec](../backend-specs/project-workbench-assets.md) 保持一致。故事大纲生成、局部改写和参考故事结构抽取接口应与 [故事大纲后端 Spec](../backend-specs/story-outline.md) 保持一致。

| 行为 | 前端方法 | 后端接口 | 请求数据 | 响应数据 | 错误处理 |
| --- | --- | --- | --- | --- | --- |
| 读取/更新项目 | `getProject` / `updateProject` | `GET/PUT /api/projects/{project_id}` | 项目基础字段 | 项目详情 | 展示项目加载或保存失败 |
| 读取世界观快照 | `listProjectWorldSnapshots` | `GET /api/projects/{project_id}/world-snapshots` | project_id | `ProjectWorldSnapshot[]`，第一版最多 1 条 | 展示世界观快照加载失败 |
| 加载世界观到项目 | `loadWorldBookToProject` | `POST /api/projects/{project_id}/world-snapshots` | `source_world_book_id`、`load_mode`、`replace_snapshot_id` | 项目世界观快照 | 目标项目已有世界观时展示单世界观限制提示 |
| 更新项目世界观快照 | `updateProjectWorldSnapshot` | `PUT /api/projects/{project_id}/world-snapshots/{snapshot_id}` | `name`、`genre`、`snapshot_content`、`entry_snapshot_content` | 更新后的项目世界观快照 | 展示保存失败，保留用户输入 |
| 移除世界观快照 | `deleteProjectWorldSnapshot` | `DELETE /api/projects/{project_id}/world-snapshots/{snapshot_id}` | project_id、snapshot_id | `{ ok: true }` | 展示世界观移除失败 |
| 读取角色快照 | `listProjectCharacterSnapshots` | `GET /api/projects/{project_id}/character-snapshots` | project_id | `ProjectCharacterSnapshot[]` | 展示角色快照加载失败 |
| 加载角色卡到项目 | `loadCharacterCardToProject` | `POST /api/projects/{project_id}/character-snapshots` | `source_character_card_id`、`load_mode`、`replace_snapshot_id` | 项目角色快照 | 同一角色卡已加载时展示不可重复加载提示 |
| 更新项目角色快照 | `updateProjectCharacterSnapshot` | `PUT /api/projects/{project_id}/character-snapshots/{snapshot_id}` | `name`、`gender`、`role_type`、`snapshot_content`、视觉与参考图字段 | 更新后的项目角色快照 | 展示保存失败，保留用户输入 |
| 移除角色快照 | `deleteProjectCharacterSnapshot` | `DELETE /api/projects/{project_id}/character-snapshots/{snapshot_id}` | project_id、snapshot_id | `{ ok: true }` | 展示角色移除失败 |
| 列出可用世界观（用于选择） | `listWorldBooks` | `GET /api/world-books` | `status=active` | active 世界观列表 | 展示可用世界观加载失败 |
| 列出可用角色卡（用于选择） | `listCharacterCards` | `GET /api/character-cards` | `status=active` | active 角色卡列表 | 展示可用角色卡加载失败 |
| 读取/保存整体大纲 | `getProjectStoryOutline` / `updateProjectStoryOutline` | `GET/PUT /api/projects/{project_id}/story-outline` | 整体大纲字段 | 整体大纲 | 展示大纲加载或保存失败 |
| 读取/保存分集大纲 | `listProjectEpisodeOutlines` / `updateProjectEpisodeOutline` | `GET /api/projects/{project_id}/episode-outlines`，`PUT /api/projects/{project_id}/episode-outlines/{episode_no}` | 分集大纲字段 | 分集大纲 | 展示分集大纲加载或保存失败 |
| 读取/保存单集内容 | `getProjectEpisodeContent` / `updateProjectEpisodeContent` | `GET/PUT /api/projects/{project_id}/episode-contents/{episode_no}` | 单集内容字段 | 单集内容 | 展示单集内容加载或保存失败 |
| 读取/保存剧本 | `getProjectEpisodeScript` / `updateProjectEpisodeScript` | `GET/PUT /api/projects/{project_id}/episode-scripts/{episode_no}` | 剧本字段 | 剧本 | 展示剧本加载或保存失败 |
| 分镜镜头列表 | `listProjectStoryboardShots` | `GET /api/projects/{project_id}/storyboard-shots/{episode_no}` | episode_no | 分镜镜头列表 | 展示分镜加载失败 |
| 新增分镜镜头 | `createProjectStoryboardShot` | `POST /api/projects/{project_id}/storyboard-shots/{episode_no}` | 镜头字段 | 分镜镜头 | 展示分镜新增失败 |
| 更新分镜镜头 | `updateProjectStoryboardShot` | `PUT /api/projects/{project_id}/storyboard-shots/{episode_no}/{shot_id}` | 镜头字段 | 分镜镜头 | 展示分镜保存失败 |
| 删除分镜镜头 | `deleteProjectStoryboardShot` | `DELETE /api/projects/{project_id}/storyboard-shots/{episode_no}/{shot_id}` | shot_id | `{ ok: true }` | 展示分镜删除失败 |
| 读取/保存文案 | `getProjectCopywriting` / `updateProjectCopywriting` | `GET/PUT /api/projects/{project_id}/copywriting/{episode_no}` | 文案字段 | 文案 | 展示文案加载或保存失败 |

## 5. 数据与迁移

- 项目工作台 v1 依赖项目创作产物表和资产快照表。
- 资产快照相关数据库、接口和状态传播规则由 [项目工作台资产快照后端 Spec](../backend-specs/project-workbench-assets.md) 定义。
- 本页面只负责在后端接口可用时展示加载、编辑、保存和错误状态。

## 6. 验收标准

- 项目列表可进入 `/projects/[id]`，创建项目成功后直接进入工作台。
- 工作台阶段导航可切换，窄屏不横向撑破页面。
- 基础信息保存、校验、时长影响提示正常。
- 世界观和角色快照为空/非空展示正常，移除后列表刷新且原资产不被删除。
- 可在"世界观与角色"tab 内直接打开资产选择面板，选择并加载世界观或角色卡到项目。
- 每个项目最多只能加载一个世界观；已有世界观时，世界观继续加载入口禁用或展示明确阻止提示。
- 项目可以加载多个角色；同一角色卡已加载时，在资产选择面板中显示为"已加载"且不可重复选择。
- 用户可以编辑并保存项目世界观快照，刷新后微调内容仍存在。
- 用户可以编辑并保存项目角色快照，刷新后微调内容仍存在。
- 保存项目世界观或项目角色微调内容不会修改世界观库或角色卡库原始内容。
- 加载成功后快照列表自动刷新，下游内容标记为"需要检查"。
- 保存项目世界观或项目角色微调内容后，下游内容标记为"需要检查"。
- 资产选择面板提供"前往资产库管理"入口。
- 整体故事大纲、分集大纲、单集内容、剧本、分镜、文案均可保存并回显。
- 上游内容变更后，下游已存在内容显示“需要检查”。
- `npm --prefix apps/web run typecheck` 通过。

## 7. 非目标

- 不接 AI 生成。
- 不做项目内快照与来源资产的复杂差异对比。
- 不做资产库新版本自动同步到项目快照。
- 不做完整视频生成和素材导出。

## 8. 生成结果编辑区

用途：

- 展示 AI 输出。
- 支持人工编辑。
- 支持重新生成和局部改写。

核心操作：

- 保存：将当前编辑内容保存为最新版本。
- 重新生成：丢弃当前内容，重新调用 AI 生成。
- 局部改写：选中部分内容，要求 AI 针对选中部分重新生成。
- 使用当前版本：确认当前内容为最终版本，状态标记为已确认。
- 查看历史版本：浏览和对比过往保存的版本。

## 9. 人物示意图确认区

用途：

- 展示人物视觉描述。
- 展示图片提示词和生成结果。
- 支持重新生成和确认。

核心操作：

- 生成示意图：基于人物文字设定生成人物示意图。
- 重新生成：对结果不满意时重新生成。
- 确认为参考形象：确认当前示意图为该角色的参考形象。
- 查看图片提示词：查看用于生成该图片的完整提示词。
