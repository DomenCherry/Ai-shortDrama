# 后端接口 Spec：分镜制作

## 1. 适用范围

本文档定义短剧制作中“分镜”工作台的后端接口、数据对象、状态传播和镜头级文生视频任务规则。

覆盖能力：

- 按集读取场次化正式分镜聚合。
- 按剧本场次生成候选镜头草稿，并采用为正式镜头。
- 新增、编辑、复制、删除、排序和重新归属镜头。
- 维护镜头提示词、Seedance 适配提示词和提示词新鲜度。
- 从单镜头调用当前启用的视频模型配置创建视频生成任务。
- 刷新、取消、采用视频生成结果，并保留候选历史。

不覆盖能力：

- 结构化剧本的创建、改写和确认，见 [结构化剧本](./structured-script.md)。
- 后期准备、字幕、配音和完整制作包导出。
- 一键整集批量生成完整视频成片。
- 在线剪辑、转码和素材库管理。

## 2. 核心后端规则

### 2.1 剧本与分镜关系

- 结构化剧本是分镜的上游输入；分镜不是剧本编辑器。
- 一个项目同一集最多存在一个当前正式 `ProjectStoryboard`。
- `ProjectStoryboard` 创建时记录 `source_script_id`、`source_script_version` 和 `source_script_status`。
- 剧本场次决定分镜的场次分组；镜头通过 `source_scene_id` 归属到剧本场次。
- 镜头可通过 `source_block_ids` 引用一个或多个剧本内容块。
- 镜头对白、旁白、画面、动作和提示词是制作快照，编辑后不得反向修改结构化剧本。
- 剧本变化后，已有分镜和镜头保留，并标记为 `needs_review`。
- 来源场次不存在或被删除时，镜头保留，`source_status` 派生为 `scene_deleted` 或 `unassigned`。

### 2.2 状态定义

分镜、镜头和相关制作内容使用：

- `draft`：草稿。
- `pending_review`：待确认。
- `confirmed`：已确认。
- `needs_review`：上游或来源变化后需要复核。

视频生成任务状态：

- `queued`：已创建或已提交，等待供应商处理。
- `running`：供应商正在生成。
- `succeeded`：生成成功。
- `failed`：生成失败。
- `canceled`：本地取消或供应商取消。

### 2.3 写入边界

分镜服务只能写入：

- `project_storyboards`
- `project_storyboard_shots`
- `project_shot_prompts`
- `project_shot_video_generations`

分镜服务不得修改：

- 项目世界观和项目角色快照。
- 整体故事大纲、分集大纲和单集故事正文。
- 结构化剧本场次和内容块。

### 2.4 状态传播

- 结构化剧本实质变化后，同集分镜、镜头、后期准备和制作包应标记为 `needs_review`。
- 镜头核心字段、排序、归属、提示词发生实质变化后，后期准备和制作包应标记为 `needs_review`。
- 采用、取消视频结果只更新镜头级视频素材采用状态，不标记制作包或其他下游内容为 `needs_review`。
- 仅展示编号派生变化不单独触发下游状态传播。

## 3. 数据对象

### 3.1 ProjectStoryboard

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 分镜聚合 ID |
| project_id | string | 项目 ID |
| episode_no | integer | 集数 |
| version | integer | 正式分镜版本 |
| revision | integer | 并发控制修订号 |
| source_script_id | string \| null | 来源结构化剧本 ID |
| source_script_version | integer \| null | 来源剧本版本 |
| source_script_status | string \| null | 来源剧本状态 |
| total_duration_seconds | number | 正式镜头总时长 |
| status | draft / pending_review / confirmed / needs_review | 分镜状态 |
| confirmed_at | datetime \| null | 确认时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.2 StoryboardSceneGroup

响应中按剧本场次派生，不需要单独持久化。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| scene_id | string \| null | 来源场次 ID，未归属时为空 |
| scene_no | integer \| null | 剧本场次展示序号 |
| display_code | string | 场次展示编号，如 `S01` 或 `U` |
| title | string | 场次标题 |
| script_duration_seconds | number \| null | 剧本场次生效时长 |
| shots_duration_seconds | number | 镜头总时长 |
| duration_deviation_percent | number \| null | 与剧本时长偏差 |
| status | draft / pending_review / confirmed / needs_review | 场次镜头汇总状态 |
| shots | ProjectStoryboardShot[] | 镜头列表 |

### 3.3 ProjectStoryboardShot

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 稳定镜头 ID |
| project_id | string | 项目 ID |
| episode_no | integer | 集数 |
| storyboard_id | string | 所属分镜 |
| source_scene_id | string \| null | 来源剧本场次 |
| display_code | string | 派生展示编号，如 `S01-001` |
| sort_order | integer | 场次内排序 |
| revision | integer | 镜头修订号 |
| shot_size | string \| null | 景别 |
| subject_description | string \| null | 主体 |
| visual_description | string \| null | 核心画面 |
| action | string \| null | 动作 |
| duration_seconds | number \| null | 镜头时长，保存时必须大于 0 |
| camera_angle | string \| null | 机位或角度 |
| camera_movement | string \| null | 运镜 |
| composition | string \| null | 构图 |
| character_snapshot_ids | string[] | 出镜角色快照 |
| expression | string \| null | 表情 |
| environment | string \| null | 环境 |
| props | string[] | 道具 |
| source_block_ids | string[] | 来源剧本内容块 |
| dialogue_snapshot | string \| null | 制作对白快照 |
| voiceover_snapshot | string \| null | 制作旁白快照 |
| sound_effect | string \| null | 音效 |
| music_note | string \| null | 音乐 |
| continuity_note | string \| null | 连续性备注 |
| source_status | valid / changed / scene_deleted / unassigned | 来源状态 |
| status | draft / pending_review / confirmed / needs_review | 镜头状态 |
| prompt | ShotPrompt | 镜头提示词 |
| prompt_freshness | current / needs_update | 提示词新鲜度 |
| prompt_customized | boolean | 是否存在人工提示词修改 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

`shot_size`、`camera_angle`、`camera_movement`、`composition`、`expression` 在前端以预设下拉为主，但后端仍按字符串保存，允许保留历史值和自定义导演术语。

### 3.4 ShotPrompt

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| image_prompt | string \| null | 通用图片提示词 |
| video_prompt | string \| null | 通用视频提示词 |
| negative_prompt | string \| null | 负面提示词 |
| first_frame_description | string \| null | 首帧描述 |
| last_frame_description | string \| null | 尾帧描述 |
| reference_asset_ids | string[] | 参考素材 |
| aspect_ratio | string \| null | 画幅 |
| seedance_prompt | string \| null | Seedance 适配提示词 |

提示词保存时必须记录内部 `source_shot_revision` 和 `customized/freshness` 状态。核心镜头字段变化后，已有提示词应标记为 `needs_update`，不得自动覆盖人工修改。

### 3.5 ProjectShotVideoGeneration

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 视频生成记录 ID |
| project_id | string | 项目 ID |
| episode_no | integer | 集数 |
| storyboard_id | string | 分镜 ID |
| shot_id | string | 镜头 ID |
| prompt_id | string \| null | 使用的提示词记录 |
| source_shot_revision | integer | 提交时镜头修订号 |
| source_prompt_revision | integer \| null | 提交时提示词修订号 |
| video_prompt_snapshot | string | 后端组装后实际提交给模型的提示词快照 |
| negative_prompt_snapshot | string \| null | 负面词快照 |
| reference_asset_ids | string[] | 提交时参考素材 |
| model_config_id | string | 使用的视频模型配置 |
| model_name | string | 模型名称 |
| provider_preset | string \| null | 供应商预设 |
| provider_task_id | string \| null | 供应商任务 ID |
| status | queued / running / succeeded / failed / canceled | 任务状态 |
| result_url | string \| null | 视频结果 URL |
| local_asset_path | string \| null | 本地素材路径 |
| thumbnail_url | string \| null | 缩略图 |
| duration_seconds | number \| null | 视频时长 |
| width | integer \| null | 宽度 |
| height | integer \| null | 高度 |
| error_message | string \| null | 可展示失败原因 |
| request_payload_snapshot | object | 脱敏请求快照 |
| elapsed_ms | integer \| null | 耗时 |
| adopted | boolean | 是否为当前采用素材 |
| adopted_at | datetime \| null | 采用时间 |
| is_stale | boolean | 响应派生字段，是否可能过期 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 4. 接口定义

### 4.1 查询分镜聚合

```text
GET /api/projects/{project_id}/storyboards/{episode_no}
```

响应：

- `200`：`ProjectStoryboard | null`。
- `400`：集数非法。
- `404`：项目不存在。

业务要求：

- 按来源剧本场次分组返回镜头。
- 如当前没有分镜但有结构化剧本，响应仍可为 `null`；前端可以基于剧本场次显示空场次。
- `display_code` 由服务端派生，不由客户端保存。

### 4.2 生成单场分镜

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/scenes/{scene_id}/generate
```

业务要求：

- 校验场次属于当前集结构化剧本。
- 以场次和内容块为输入生成候选镜头草稿。
- 第一版允许直接写入正式草稿镜头；后续候选采用能力落地后，应先保存候选记录再采用。
- 不修改结构化剧本。

### 4.3 新增镜头

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/shots
```

请求体：`ProjectStoryboardShotPayload`。

业务要求：

- 如果当前集没有分镜，自动创建 `ProjectStoryboard` 并记录当前结构化剧本来源。
- `source_scene_id` 为空时创建未归属镜头。
- `source_scene_id` 非空时必须属于当前分镜来源剧本。
- 写入后重新派生排序和展示编号。

### 4.4 更新镜头

```text
PUT /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}
```

请求体：`ProjectStoryboardShotPayload`，必须带当前 `revision`。

业务要求：

- 校验镜头属于当前项目、集数和分镜。
- `revision` 不匹配时返回 `409`。
- 更新核心字段后镜头 `revision += 1`。
- 核心字段变化后将提示词标记为 `needs_update`。
- 不修改结构化剧本或项目资产快照。

### 4.5 删除镜头

```text
DELETE /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}
```

业务要求：

- 删除镜头及其提示词。
- 不删除视频生成历史；首版采用删除限制，镜头已有任意视频生成记录时禁止删除该镜头。
- 重新计算场次排序、展示编号和总时长。

### 4.6 复制镜头

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/duplicate
```

业务要求：

- 复制核心镜头字段、声音字段、提示词字段和参考素材。
- 新镜头使用新的稳定 ID，插入到目标场次末尾。
- 视频生成历史不复制。

### 4.7 重新归属镜头

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/reassign
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| source_scene_id | string | 是 | 新来源场次 ID |

业务要求：

- 新场次必须属于当前分镜来源剧本。
- 移动后插入新场次末尾并重新编号。
- 不自动改变镜头制作文本和提示词。

### 4.8 场次内排序

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/scenes/{scene_id}/reorder
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| shot_ids | string[] | 是 | 该场次内完整镜头 ID 顺序 |

业务要求：

- `shot_ids` 必须完整覆盖该场次当前镜头集合。
- 排序只影响该场次内镜头。
- 排序后重新派生展示编号。

### 4.9 查询镜头视频生成历史

```text
GET /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations
```

响应：

- `200`：`ProjectShotVideoGeneration[]`，按创建时间倒序。
- `404`：项目、分镜或镜头不存在。

业务要求：

- 响应中派生 `is_stale`：当生成记录的 `source_shot_revision` 或 `source_prompt_revision` 落后于当前镜头或提示词时为 true。

### 4.10 创建单镜头视频生成任务

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resolution | string | 否 | 本次生成分辨率，首版支持 `720p`、`1080p`；不传时默认 `720p` |
| aspect_ratio | string | 否 | 本次生成画幅，首版支持 `16:9`、`9:16`、`1:1`、`4:3`、`3:4`、`21:9`；不传时使用提示词画幅，仍为空则默认 `16:9` |
| duration_seconds | number | 否 | 本次生成时长；不传时使用镜头时长，仍为空则默认 4 秒 |

业务要求：

- 使用当前启用且最近测试成功的 `config_type=video` 模型配置。
- 首版默认使用 Seedance 适配器；无 Seedance 预设时可走通用视频生成接口。
- 提示词优先级：`seedance_prompt` 优先；缺失时使用 `video_prompt`。
- 后端必须统一组装最终视频提示词，并把组装结果保存到 `video_prompt_snapshot`。
- 最终视频提示词必须包含基础提示词、出镜角色视觉锚点、关键镜头视觉字段、首尾帧约束和负面提示词。
- 角色视觉锚点来自 `character_snapshot_ids` 对应的项目角色快照，使用 `name`、`gender`、`role_type`、`visual_description`；参考图只记录风险和素材状态，首版不发送给 Seedance 文生视频请求。
- 关键镜头视觉字段包括 `subject_description`、`visual_description`、`action`、`shot_size`、`camera_angle`、`camera_movement`、`composition`、`expression`、`environment`、`props`。
- `dialogue_snapshot`、`voiceover_snapshot`、`sound_effect`、`music_note`、`source_block_ids`、`source_scene_id`、`continuity_note`、`image_prompt` 不直接进入文生视频请求。
- 分辨率、画幅、时长为单次生成参数，不写回模型配置、镜头或提示词。
- 缺少可用提示词时返回明确错误。
- 提示词为 `needs_update` 时第一版阻止生成。
- 保存输入快照、模型配置、请求 payload 快照和供应商任务 ID。
- 供应商提交失败时保留本地生成记录并写入 `failed` 和 `error_message`。
- 不修改镜头核心字段、提示词或已有采用素材。

### 4.11 刷新视频生成任务

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/refresh
```

业务要求：

- 使用生成记录保存的 `model_config_id` 查询供应商任务，不使用当前新切换的模型配置。
- 将供应商状态映射为 `queued/running/succeeded/failed/canceled`。
- 成功时保存 `result_url`、`thumbnail_url`、`duration_seconds`、`width`、`height` 等可获得元信息。
- 失败时保存可读失败原因。

### 4.12 采用视频结果

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/adopt
```

业务要求：

- 只能采用 `succeeded` 且存在结果引用的生成记录。
- 同一镜头最多一条记录 `adopted=true`。
- 采用时将同镜头其他记录 `adopted=false`。
- 采用结果不修改镜头核心字段、提示词或剧本来源。
- 采用结果不标记制作包或其他下游内容为 `needs_review`；制作包导出时按当前采用结果读取素材引用。

### 4.13 取消视频任务

```text
POST /api/projects/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/cancel
```

业务要求：

- 首版只更新本地状态为 `canceled`。
- 若供应商后续支持取消，再调用供应商取消接口。
- 已成功或已失败的任务不得取消。

## 5. 错误提示

| 场景 | HTTP | message |
| --- | --- | --- |
| 项目不存在 | 404 | 项目不存在 |
| 集数非法 | 400 | 集数编号必须在项目集数范围内 |
| 分镜不存在 | 404 | 项目分镜不存在 |
| 镜头不存在 | 404 | 项目分镜不存在 |
| 来源场次非法 | 400 | 来源场次不属于当前集剧本 |
| 修订冲突 | 409 | 分镜已在其他操作中更新 |
| 缺少视频提示词 | 400 | 请先填写视频提示词 |
| 视频模型未配置 | 400 | 请先配置并启用视频生成模型 |
| 视频模型未测试成功 | 400 | 视频生成模型暂不可用，请先完成接口测试 |
| 视频生成记录不存在 | 404 | 视频生成记录不存在 |
| 镜头已有视频生成记录 | 400 | 镜头已有视频生成记录，暂不支持删除 |
| 采用失败 | 400 | 只能采用已生成成功的视频结果 |

## 6. 验收标准

- 分镜聚合能按剧本场次返回镜头分组。
- 分镜创建时记录来源剧本 ID、版本和状态。
- 镜头新增、编辑、复制、删除、排序和重新归属均不修改结构化剧本。
- 更新镜头时正确校验 `revision`。
- 镜头核心字段变化后，提示词标记为 `needs_update`。
- 来源剧本变化后，分镜和镜头保留并标记为 `needs_review`。
- 镜头已有视频生成记录时删除镜头返回明确错误，且不删除视频生成历史。
- 视频任务创建会校验启用且测试成功的视频模型。
- `seedance_prompt` 优先于 `video_prompt`。
- 视频任务失败不覆盖已采用素材；失败任务重试允许覆盖原失败记录的任务状态和结果字段。
- 刷新任务能保存成功、失败和进行中状态。
- 同一镜头最多一个视频结果 `adopted=true`。
- 已采用结果在镜头或提示词变化后响应中显示 `is_stale=true`。

## 7. 关联文档

- [分镜制作模块 PRD](../module-prds/production/storyboard-production.md)
- [分镜制作前端 Spec](../frontend-specs/storyboard-production.md)
- [结构化剧本后端 Spec](./structured-script.md)
- [模型 API 配置后端 Spec](./model-api-settings.md)
