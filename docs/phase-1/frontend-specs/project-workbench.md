# 项目工作台页面 Spec

## 1. 页面目标

- 页面路径：`/projects/[id]`
- 目标：把项目从基础资料管理升级为短剧创作工作台，承接“项目设定 -> 世界观与角色 -> 故事大纲 -> 分集大纲 -> 单集内容 -> 剧本 -> 分镜与文案”的完整人工编辑流程。
- 当前阶段不做 AI 生成，只搭建可保存、可检查、可继续迭代的项目内创作结构。

## 2. 信息架构

- 项目概览：项目名称、状态、题材、平台、集数、单集时长、总时长、创意描述、更新时间。
- 阶段导航：基础信息、世界观与角色、故事大纲、分集大纲、单集内容、剧本、分镜与文案。
- 基础信息：复用项目创建字段，支持保存和还原。
- 世界观与角色：展示已加载项目快照，支持跳转资产库和从项目移除。
- 故事大纲：一句话故事、核心冲突、主线目标、人物弧光、结局方向、补充说明、状态。
- 分集大纲：按项目集数展示分集表，单集编辑标题、梗概、钩子、冲突、反转、悬念、预计时长、状态。
- 单集内容：按集维护详细剧情内容和关键剧情节拍。
- 剧本：按集维护场景说明、对白、动作说明和旁白。
- 分镜与文案：按集维护镜头列表、字幕、平台标题、平台简介、发布文案。

## 3. 交互规则

- 工作台加载失败时显示中文错误，并保留返回项目管理入口。
- 保存项目设定时继续执行创意、集数、单集时长和总时长校验。
- 修改项目设定、移除项目世界观或角色后，下游创作内容标记为 `needs_review`。
- 保存整体故事大纲后，分集大纲、单集内容、剧本、分镜和文案标记为 `needs_review`。
- 保存分集大纲后，同集单集内容、剧本、分镜和文案标记为 `needs_review`。
- 保存单集内容后，同集剧本、分镜和文案标记为 `needs_review`。
- 保存剧本后，同集分镜和文案标记为 `needs_review`。
- 前端成功提示应覆盖真实影响范围，不能只提示部分下游内容。
- 状态支持 `draft`、`confirmed`、`needs_review`，前端展示为“草稿”“已确认”“需要检查”。
- 删除项目内快照只影响项目副本，不影响世界观库或角色卡库原始资产。

## 4. API 依赖

| 行为 | 前端方法 | 后端接口 |
| --- | --- | --- |
| 读取/更新项目 | `getProject` / `updateProject` | `GET/PUT /api/projects/{project_id}` |
| 读取/移除世界观快照 | `listProjectWorldSnapshots` / `deleteProjectWorldSnapshot` | `GET/DELETE /api/projects/{project_id}/world-snapshots...` |
| 读取/移除角色快照 | `listProjectCharacterSnapshots` / `deleteProjectCharacterSnapshot` | `GET/DELETE /api/projects/{project_id}/character-snapshots...` |
| 读取/保存整体大纲 | `getProjectStoryOutline` / `updateProjectStoryOutline` | `GET/PUT /api/projects/{project_id}/story-outline` |
| 读取/保存分集大纲 | `listProjectEpisodeOutlines` / `updateProjectEpisodeOutline` | `GET /api/projects/{project_id}/episode-outlines`，`PUT /api/projects/{project_id}/episode-outlines/{episode_no}` |
| 读取/保存单集内容 | `getProjectEpisodeContent` / `updateProjectEpisodeContent` | `GET/PUT /api/projects/{project_id}/episode-contents/{episode_no}` |
| 读取/保存剧本 | `getProjectEpisodeScript` / `updateProjectEpisodeScript` | `GET/PUT /api/projects/{project_id}/episode-scripts/{episode_no}` |
| 分镜镜头列表 | `listProjectStoryboardShots` | `GET /api/projects/{project_id}/storyboard-shots/{episode_no}` |
| 新增分镜镜头 | `createProjectStoryboardShot` | `POST /api/projects/{project_id}/storyboard-shots/{episode_no}` |
| 更新分镜镜头 | `updateProjectStoryboardShot` | `PUT /api/projects/{project_id}/storyboard-shots/{episode_no}/{shot_id}` |
| 删除分镜镜头 | `deleteProjectStoryboardShot` | `DELETE /api/projects/{project_id}/storyboard-shots/{episode_no}/{shot_id}` |
| 读取/保存文案 | `getProjectCopywriting` / `updateProjectCopywriting` | `GET/PUT /api/projects/{project_id}/copywriting/{episode_no}` |

## 5. 数据与迁移

- 项目工作台 v1 依赖项目创作产物表：整体故事大纲、分集大纲、单集内容、剧本、分镜镜头和文案。
- 后端新增或更新这些表后，真实环境必须执行数据库迁移。
- 后端服务必须重启到包含新接口的版本，否则前端会显示接口或资源不存在。

## 6. 验收标准

- 项目列表可进入 `/projects/[id]`，创建项目成功后直接进入工作台。
- 工作台阶段导航可切换，窄屏不横向撑破页面。
- 基础信息保存、校验、时长影响提示正常。
- 世界观和角色快照为空/非空展示正常，移除后列表刷新且原资产不被删除。
- 整体故事大纲、分集大纲、单集内容、剧本、分镜、文案均可保存并回显。
- 上游内容变更后，下游已存在内容显示“需要检查”。
- 执行数据库迁移并重启后端后，新接口可正常访问。
- `npm --prefix apps/web run typecheck` 通过。

## 7. 非目标

- 不接 AI 生成。
- 不做项目内世界观/角色副本编辑。
- 不做完整视频生成和素材导出。
