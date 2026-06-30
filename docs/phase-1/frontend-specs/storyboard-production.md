# 分镜制作工作台页面 Spec

## 1. 页面目标

- 页面路径：`/projects/[id]/production`，短剧制作模块下的“分镜”入口。
- 所属阶段：第一期，短剧制作 / 分镜制作。
- 关联 PRD：[分镜制作](../module-prds/production/storyboard-production.md)。
- 关联后端 Spec：[分镜制作后端接口](../backend-specs/storyboard-production.md)。

本页面把当前集结构化剧本场次拆成可制作镜头，并在镜头详情内维护提示词、视频生成任务、候选视频结果和已采用镜头素材。

首版重点：

- 场次化分镜浏览与镜头编辑。
- 剧本来源关系可见。
- 单镜头文生视频生成闭环。

非目标：

- 不在本页面编辑结构化剧本。
- 不做一键整集完整视频生成。
- 不做在线视频剪辑器或复杂素材库。

## 2. 信息架构

```text
短剧制作
  -> 剧本
  -> 分镜
     -> 场次化镜头导航
     -> 镜头详情
        -> 核心画面
        -> 声音
        -> 提示词
        -> 视频生成
        -> 参考与检查
  -> 后期准备
  -> 制作包
```

页面应保持工作台型高信息密度布局：

- 顶部：集数切换、来源剧本版本、当前剧本版本、分镜状态、镜头数量、总时长、主要操作。
- 左侧：按剧本场次分组的镜头导航。
- 中部：当前镜头详情表单。
- 底部：连续性条，展示当前镜头前后各 2 镜。
- 抽屉：窄屏镜头导航。

## 3. 剧本与分镜关系展示

页面必须明确展示：

- 分镜来源剧本版本和状态。
- 当前剧本版本和状态。
- 当前分镜是否落后于当前剧本。
- 当前镜头归属的剧本场次。
- 当前镜头引用的剧本内容块数量。
- 镜头文本是制作快照，编辑后不会反向修改剧本。

当来源剧本和当前剧本不一致时：

- 顶部展示“当前剧本已变化，请复核分镜来源”。
- 分镜状态为 `needs_review` 时使用警示样式。
- 不自动覆盖镜头字段、提示词或视频结果。

## 4. 场次与镜头导航

左侧镜头导航按 `StoryboardSceneGroup` 渲染：

- 场次编号，如 `S01`。
- 场次标题。
- 镜头数量。
- 场次镜头总时长。
- 生成状态：生成中 / 成功 / 失败。

场次为空时：

- 展示“生成”入口。
- 生成失败时展示“重试”入口。
- 已有镜头的场次不默认重新生成，避免覆盖人工修改。

镜头项展示：

- 展示编号，如 `S01-001`。
- 景别。
- 时长。
- 主体或核心画面摘要。
- 当前选中态。

镜头排序：

- 支持同一场次内上移 / 下移。
- 排序前如当前镜头有未保存修改，应先提示保存或放弃。
- 排序成功后刷新分镜聚合和展示编号。

## 5. 镜头详情

### 5.1 顶部状态

展示：

- 当前镜头展示编号。
- 镜头状态：草稿、待审核、已确认、需检查。
- 提示词是否需要更新。
- 保存、复制、删除操作。

镜头状态允许用户切换，但进入 `confirmed` 前应保留后端结构校验能力。

### 5.2 核心画面 Tab

字段：

| 字段 | 控件 | 说明 |
| --- | --- | --- |
| 景别 | 输入框或选项 | 例如特写、中景、全景 |
| 时长 | 数字输入 | 必须大于 0 |
| 主体 | 多行文本 | 人物、环境、物体或视觉主体 |
| 核心画面 | 多行文本 | 镜头画面描述 |
| 动作 | 多行文本 | 主体动作或画面变化 |
| 连续性备注 | 多行文本 | 前后镜衔接 |
| 机位 / 角度 | 输入框 | 可选 |
| 运镜 | 输入框 | 可选 |
| 构图 | 多行文本 | 可选 |
| 环境 | 多行文本 | 可选 |

### 5.3 声音 Tab

字段：

- 对白。
- 旁白。
- 音效。
- 音乐。

这些字段是制作快照，不直接写回结构化剧本内容块。

### 5.4 提示词 Tab

字段：

- 图片提示词。
- 视频提示词。
- 负面词。
- Seedance 提示词。
- 首帧描述。
- 尾帧描述。

交互规则：

- 用户编辑提示词后，服务端应将提示词标记为人工修改。
- 核心镜头字段变化后，页面展示“提示词需更新”。
- 修改 Seedance 提示词不反向修改核心镜头字段或通用视频提示词。

### 5.5 视频生成 Tab

视频生成 Tab 放在“提示词”之后。

展示内容：

- 本次将使用的提示词，优先显示 `seedance_prompt`，缺失时显示 `video_prompt`。
- 当前视频模型配置状态。
- 本次生成参数：分辨率、画幅和时长。
- 生成视频按钮。
- 刷新状态按钮。
- 失败重试入口。
- 当前已采用视频结果。
- 历史候选视频结果列表。

生成按钮禁用条件：

- 当前镜头有未保存修改。
- 缺少 `seedance_prompt` 和 `video_prompt`。
- 提示词状态为 `needs_update`。
- 没有启用的视频模型配置。
- 启用视频模型的 `last_test_status != success`。
- 本次生成时长非法。

按钮禁用时必须展示明确原因。

本次生成参数规则：

- 参数只影响当前创建的视频生成任务，不写回镜头、提示词或模型配置。
- 分辨率默认不调整，由后端使用 `720p`；用户可手动选择 `720p` 或 `1080p`。
- 画幅默认不调整，由后端优先使用提示词 `aspect_ratio`，没有则使用 `16:9`；用户可手动选择 `16:9`、`9:16`、`1:1`、`4:3`、`3:4`、`21:9`。
- 时长默认不调整，由后端使用镜头时长；用户可为本次生成输入临时时长。

候选视频卡片展示：

- 视频预览或缩略图。
- 任务状态：排队中、生成中、成功、失败、已取消。
- 是否已采用。
- 是否可能过期。
- 提示词快照摘要。
- 失败原因。
- 刷新、取消、采用、打开结果等操作。

采用结果规则：

- 只能采用成功且有结果引用的视频。
- 采用某个结果只改变该镜头的视频素材采用状态。
- 采用结果不修改镜头核心字段、提示词或来源剧本关系。
- 同一镜头最多一个候选结果显示为已采用。

失败重试规则：

- 失败任务的“重试”可以复用原视频生成记录，重新提交供应商任务并覆盖该记录的任务状态、供应商任务 ID、失败原因和结果字段。
- 重试只作用于该失败任务记录，不修改镜头核心字段、提示词或已采用视频结果。

### 5.6 参考与检查 Tab

展示：

- 来源剧本版本。
- 归属场次。
- 引用剧本块数量。
- 来源状态。
- 来源剧本内容块列表。
- 当前镜头引用的内容块高亮。
- 重新归属场次控件。
- 提示词状态。
- 人物素材关联数量。

重新归属规则：

- 只能选择当前剧本中的有效场次。
- 当前镜头有未保存修改时禁用，并提示先保存。
- 重新归属后不自动改写镜头制作文本和提示词。

## 6. 空状态与加载状态

页面加载：

- 分镜聚合加载中展示“正在加载分镜...”。
- 视频生成历史加载中在候选历史标题处显示“加载中...”。

无镜头：

- 如果当前集有结构化剧本场次，展示“从首个场次创建镜头并开始逐镜精修”，提供新增镜头按钮。
- 如果当前集没有结构化剧本，展示“请先完成结构化剧本场次”，不展示误导性的生成入口。

无视频结果：

- 当前采用区展示“当前镜头还没有采用的视频素材”。
- 候选历史展示“暂无视频生成记录”。

## 7. 未保存修改保护

以下操作发生前必须处理当前镜头未保存修改：

- 切换镜头。
- 切换集数。
- 切换短剧制作一级入口。
- 重新归属场次。
- 发起视频生成。

弹窗选项：

- 取消。
- 放弃修改。
- 保存并切换。

## 8. API 依赖

| 行为 | 前端方法 | 后端接口 | 错误处理 |
| --- | --- | --- | --- |
| 读取分镜聚合 | `getProjectStoryboard` | `GET /api/projects/{project_id}/storyboards/{episode_no}` | 展示分镜加载失败 |
| 生成单场分镜 | `generateProjectStoryboardScene` | `POST /api/projects/{project_id}/storyboards/{episode_no}/scenes/{scene_id}/generate` | 场次标记失败并允许重试 |
| 新增镜头 | `createProjectStoryboardShot` | `POST /api/projects/{project_id}/storyboards/{episode_no}/shots` | 展示创建镜头失败 |
| 更新镜头 | `updateProjectStoryboardShot` | `PUT /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}` | 保留本地修改，展示保存失败 |
| 删除镜头 | `deleteProjectStoryboardShot` | `DELETE /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}` | 有视频生成记录时展示后端返回原因，否则展示删除失败 |
| 复制镜头 | `duplicateProjectStoryboardShot` | `POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/duplicate` | 展示复制失败 |
| 重新归属 | `reassignProjectStoryboardShot` | `POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/reassign` | 展示重新归属失败 |
| 场次内排序 | `reorderProjectStoryboardScene` | `POST /api/projects/{project_id}/storyboards/{episode_no}/scenes/{scene_id}/reorder` | 展示排序失败 |
| 读取视频模型配置 | `listModelConfigs("video")` | `GET /api/model-configs?config_type=video` | 无配置时禁用生成按钮 |
| 读取视频历史 | `listShotVideoGenerations` | `GET /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations` | 展示读取视频生成记录失败 |
| 创建视频任务 | `createShotVideoGeneration` | `POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations` | 展示创建视频生成任务失败 |
| 刷新任务 | `refreshShotVideoGeneration` | `POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/refresh` | 展示刷新状态失败 |
| 采用结果 | `adoptShotVideoGeneration` | `POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/adopt` | 展示采用失败 |
| 取消任务 | `cancelShotVideoGeneration` | `POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/cancel` | 展示取消失败 |

## 9. 错误文案

| 场景 | 文案 |
| --- | --- |
| 分镜加载失败 | 读取分镜失败 |
| 镜头保存失败 | 保存失败 |
| 镜头已有视频生成记录 | 镜头已有视频生成记录，暂不支持删除 |
| 修订冲突 | 分镜已在其他操作中更新，请刷新后合并 |
| 重新归属被禁用 | 请先保存当前修改 |
| 无视频提示词 | 请先填写 Seedance 提示词或视频提示词 |
| 未保存不能生成 | 请先保存当前镜头修改后再生成视频 |
| 提示词需更新 | 提示词需要更新，请先保存或确认后再生成视频 |
| 无视频模型 | 请先在设置中启用视频生成模型 |
| 视频模型未测试成功 | 请先测试并通过当前视频生成模型 |
| 视频任务创建失败 | 创建视频生成任务失败 |
| 视频刷新失败 | 刷新视频生成状态失败 |
| 采用失败 | 采用视频结果失败 |

## 10. 验收标准

- 页面按剧本场次分组展示镜头。
- 顶部清楚展示来源剧本版本和当前剧本版本。
- 来源剧本变化时展示复核提示。
- 镜头详情能编辑核心画面、声音、提示词、参考关系。
- 参考与检查 Tab 能展示镜头归属场次和引用剧本块。
- 引用剧本块在来源列表中高亮。
- 未保存修改切换镜头或集数时有保护。
- 视频生成 Tab 能展示空态、运行中、失败、成功和已采用结果。
- 生成按钮在缺少提示词、模型不可用、提示词需更新或有未保存修改时禁用并显示原因。
- 切换镜头时加载对应镜头视频生成历史。
- 失败任务可重试，并允许在原失败任务记录上覆盖新的任务状态和结果。
- 采用视频结果后，同一镜头只显示一个已采用结果。
- 镜头或提示词后续变化时，已采用结果显示可能过期。
- `npm --prefix apps/web run typecheck` 通过。

## 11. 关联文档

- [分镜制作模块 PRD](../module-prds/production/storyboard-production.md)
- [分镜制作后端 Spec](../backend-specs/storyboard-production.md)
- [结构化剧本前端 Spec](./structured-script.md)
- [模型 API 配置前端 Spec](./model-api-settings.md)
