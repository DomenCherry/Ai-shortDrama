# 后端接口 Spec：结构化剧本

## 1. 适用范围

本文档定义结构化剧本的数据模型、迁移、接口合同、生成与候选采用、时长估算、一致性检查、正式版本和状态传播规则。

覆盖能力：

- 按集读取和原子保存结构化正式剧本。
- 在完整聚合内新增、编辑、删除和排序场次及内容块。
- 生成整集、重新生成单场和改写同一场内选中内容块。
- 查询、采用和放弃候选结果。
- 自动估算场次和整集时长，支持人工覆盖。
- 执行结构和语义一致性检查。
- 提交待确认和确认正式剧本。
- 保留正式版本、限制未采用候选数量。
- 迁移旧四字段剧本并传播上下游状态。

不覆盖能力：

- 分镜生成和编辑。
- 图片、视频、配音、字幕或成片生成。
- 多人实时协同和复杂版本合并。
- 自动按照检查建议修改正式内容。

本 Spec 生效后，取代 [项目工作台后端 Spec](./project-workbench.md) 中 `ProjectEpisodeScript` 四字段模型及其保存载荷；原接口路径保持不变，响应和请求升级为结构化聚合。

## 2. 核心后端规则

### 2.1 聚合与写入边界

- `EpisodeScript` 是聚合根。
- `ScriptScene` 和 `ScriptBlock` 不提供绕过剧本 service 的独立写入接口。
- 第一版通过 `PUT /episode-scripts/{episode_no}` 原子保存完整聚合，实现场次和内容块 CRUD、排序和批量校验。
- 任一校验失败时整个保存事务回滚，不允许部分场次成功。
- 服务端根据数组顺序规范化 `sort_order` 和 `scene_no`，不信任客户端提交的展示编号。
- 短剧制作接口只能读取上游快照，不得写入项目资料、资产或故事文本。

### 2.2 集数、身份与项目隔离

所有接口必须：

- 校验项目存在。
- 校验 `0 < episode_no <= project.episode_count`。
- 校验路径中的剧本、场次、内容块、候选和版本属于当前项目与集数。
- 校验 `character_snapshot_id` 属于当前项目；不得引用资产库原始角色卡或其他项目快照。
- 不向客户端返回模型 API Key、供应商密钥或内部提示词模板。

### 2.3 `revision` 与正式 `version`

- `revision`：每次正式聚合写入或状态变更递增，用于乐观并发控制。
- `version`：仅在会影响下游生产内容的实质变化时递增，用于正式历史和下游来源追溯。
- 新建正式剧本时 `revision = 1`、`version = 1`。
- 保存请求必须携带当前 `revision`；不一致返回 `409`，不得覆盖。
- 每次 `version` 递增都写入不可变 `EpisodeScriptVersion` 快照。
- 候选采用必须同时校验当前 `revision` 与候选生成时的 `base_script_version`、目标 ID 快照。

实质变化包括：

- 新增、删除、复制或排序场次。
- 修改地点、时间、内外景、人物引用、时长覆盖或剧情作用。
- 新增、删除、复制、排序或修改任一内容块字段。
- 采用任意范围候选。

仅以下变化不递增 `version`，但递增 `revision`：

- 剧本标题或场次标题。
- `draft`、`pending_review`、`confirmed`、`needs_review` 状态及确认时间。
- 服务端估算配置变化触发的纯自动时长重算。

如果同一请求同时包含实质和展示字段变化，按实质变化处理。

### 2.4 状态机

状态值：

- `draft`：正在编辑。
- `pending_review`：已完成基本结构，等待人工确认。
- `confirmed`：已确认，可作为正式制作输入。
- `needs_review`：上游变化，需要复核。

允许转换：

```text
无内容 -> draft
draft / needs_review -> pending_review
draft / pending_review / needs_review -> confirmed（通过确认接口）
confirmed / pending_review / needs_review -> draft（保存实质变化或采用候选）
任意已存在状态 -> needs_review（上游传播）
```

- 普通保存不得直接把状态设置为 `confirmed`；必须调用确认接口。
- 提交待确认和确认只改变状态与 `revision`，不增加 `version`。
- `confirmed_at` 仅在确认成功时写入；离开 `confirmed` 后保留最近确认时间用于审计，但响应语义为“最近确认时间”。

### 2.5 来源正文版本

当前 `ProjectEpisodeContent` 尚无独立整数版本。结构化剧本使用不透明字符串 `source_content_version`：

```text
{episode_content.id}:{episode_content.updated_at ISO8601}
```

- 生成和首次人工创建时保存该值；正文不存在时人工草稿可保存 `null`，但不能调用整集生成。
- 正文任意保存后，已有剧本由状态传播标记为 `needs_review`。
- 后续正文引入正式版本号时，可迁移为稳定版本 ID；客户端不得解析该字符串。

### 2.6 保存、版本与下游传播

- 保存前比较规范化后的聚合，空白差异和等值重复请求不产生新 `version`。
- 展示字段或状态变化不标记下游。
- 实质变化保存成功后，将同集已存在的分镜、后期准备和制作包标记为 `needs_review`。
- 兼容期内现有 `ProjectStoryboardShot` 和 `ProjectCopywriting` 也标记为 `needs_review`。
- 传播只更新状态，不删除、覆盖或自动重建下游内容。
- 采用候选与实质保存使用同一传播函数。

### 2.7 生成与候选隔离

- 生成服务只创建 `ScriptGeneration`，不得直接写正式聚合。
- 生成前必须有可用文本模型配置；缺失时返回 `400`。
- 整集生成必须有非空当前集故事正文。
- 场次生成要求目标场次存在于基准版本。
- 块改写要求目标块非空、互不重复、属于同一目标场次、在当前排序中连续且存在于基准版本。
- 自定义指令去除首尾空白后最长 2000 字。
- `client_request_id` 在 `(project_id, episode_no, generation_scope)` 内唯一；重复请求返回原记录，不重复调用模型。
- 输入快照必须保存生成时的项目基础信息、目标时长、世界观快照、角色快照及口吻、故事大纲、当前分集大纲、当前正文及来源版本、上一集摘要、正式剧本基准版本、目标范围、预设方向和用户指令。
- 模型输出必须先通过结构 schema 校验；无效输出不创建可采用候选，接口返回生成失败，正式内容不变。
- 候选输出使用 JSON 对象保存，不使用不可校验的拼接文本。

### 2.8 候选采用

- 采用在单个数据库事务中完成：锁定候选与正式聚合、验证基准、替换目标、重新估算、运行结构校验、写新版本、更新候选状态、传播下游。
- `episode` 采用替换完整场次集合；正式剧本 ID 保持不变，新场次和块使用新稳定 ID。
- `scene` 采用只替换目标场次的元信息和内容块；场次稳定 ID 保持不变，范围外场次及块不得变化。
- `blocks` 采用只替换目标块构成的连续区间；候选块数量可以变化，替换区间外的块 ID、内容和顺序保持不变。
- 采用后正式状态为 `draft`，`version` 和 `revision` 各递增一次。
- 只有 `candidate` 可采用或放弃；重复采用已采用候选应幂等返回当前结果，已放弃候选不可采用。
- 正式稿版本、目标场次或目标块在生成后变化时返回 `409`，不尝试自动合并。

### 2.9 候选保留

- 每集最多保留最近 20 条 `candidate` 候选。
- 新候选成功创建后，在同一事务或可靠后台任务中删除该集超出上限的最旧 `candidate`。
- `adopted` 永久保留。
- `discarded` 不计入 20 条上限；默认保留 30 天后可清理。
- 清理不得删除正式版本或正式版本引用的输入/输出审计信息。

### 2.10 时长估算

时长服务使用可配置参数，默认值：

| 内容 | 默认规则 |
| --- | --- |
| 对白 | 可见字符数 / 4.0 字符每秒；每块最少 1 秒 |
| 旁白 | 可见字符数 / 3.5 字符每秒；每块最少 1 秒 |
| 动作 | 可见字符数 / 8.0 字符每秒；每块最少 1 秒 |
| 转场 | 固定 2 秒；正文超过 16 个可见字符时按字符数 / 8.0 取较大值 |

- 可见字符不计空白；中文标点计入自然停顿，不单独加权。
- 场次 `auto_duration_seconds` 为内容块估算和，四舍五入到 0.1 秒。
- 场次 `effective_duration_seconds = manual_duration_seconds ?? auto_duration_seconds`。
- 剧本 `auto_duration_seconds` 为所有场次自动时长和。
- 剧本 `effective_duration_seconds = manual_duration_seconds ?? sum(scene.effective_duration_seconds)`。
- 人工时长必须大于 0 且不超过 3600 秒。
- 后端返回相对项目目标时长的偏差秒数和偏差百分比。
- 绝对偏差不超过 10% 为正常；大于 10% 且不超过 25% 返回 `warning`；大于 25% 返回代码 `duration_severe_deviation` 的 `warning`。时长偏差不阻止保存或确认。
- 配置变更不得静默改写历史版本；当前稿下次保存、检查或显式重算时使用新配置。

### 2.11 一致性检查

检查分两层：

- `structure`：确定性校验，不调用模型。
- `full`：先执行结构校验，再使用文本模型检查世界观、角色、剧情目标、口吻和钩子。

结构错误至少包括：

- 剧本无场次。
- 场次缺少地点、时间或内外景。
- 场次无非空内容块。
- 内容块类型非法或正文为空。
- 对白既无有效角色引用也无临时人物名称。
- ID 重复、目标归属错误或排序无法规范化。

完整检查至少包括：

- 世界观规则冲突。
- 人物身份、关系、目标、秘密和出场合理性冲突。
- 人物口吻明显偏离。
- 分集剧情目标、开场钩子、冲突、反转或结尾悬念缺失。
- 时长偏离项目目标。

- `error` 阻止提交待确认和确认。
- `warning`、`info` 不阻止保存或确认。
- 检查结果必须记录 `script_version`、`script_revision` 和输入快照摘要；旧结果不能用于确认新版本。
- 完整检查模型失败时仍返回结构检查结果，并标记 `semantic_check_status = failed`；用户可保存，但确认必须至少有当前版本成功的结构检查。语义检查失败不作为结构错误。

## 3. 数据对象

### 3.1 EpisodeScript

表示某项目某一集的当前正式聚合。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 剧本稳定 ID |
| project_id | string | 项目 ID |
| episode_no | integer | 集数 |
| title | string \| null | 剧本标题 |
| revision | integer | 每次写入递增的并发修订号 |
| version | integer | 实质内容正式版本号 |
| source_content_version | string \| null | 来源正文不透明版本 |
| auto_duration_seconds | number | 自动估算总时长 |
| manual_duration_seconds | number \| null | 人工覆盖总时长 |
| effective_duration_seconds | number | 最终生效总时长 |
| target_duration_seconds | number | 响应时派生的项目目标时长 |
| duration_deviation_seconds | number | 生效时长减目标时长 |
| duration_deviation_percent | number | 相对目标偏差百分比 |
| status | draft / pending_review / confirmed / needs_review | 剧本状态 |
| confirmed_at | datetime \| null | 最近确认时间 |
| scenes | ScriptScene[] | 按 `sort_order` 升序的场次 |
| validation_issues | ScriptCheckIssue[] | 当前聚合的确定性结构问题 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.2 ScriptScene

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 场次稳定 ID |
| script_id | string | 所属剧本 ID |
| scene_no | integer | 响应派生展示号，从 1 连续递增 |
| title | string \| null | 场次标题 |
| location | string | 地点 |
| time_of_day | morning / day / dusk / night / other | 时间 |
| interior_exterior | interior / exterior / mixed | 内外景 |
| character_refs | ScriptCharacterRef[] | 项目角色快照引用 |
| auto_duration_seconds | number | 自动估算时长 |
| manual_duration_seconds | number \| null | 人工覆盖时长 |
| effective_duration_seconds | number | 最终生效时长 |
| story_purpose | string \| null | 剧情作用 |
| sort_order | integer | 服务端规范化排序值 |
| blocks | ScriptBlock[] | 按 `sort_order` 升序的块 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

`ScriptCharacterRef` 至少返回 `character_snapshot_id`、`name` 和当前快照 `updated_at`，其中名称是便于展示的响应快照，不替代外键校验。

### 3.3 ScriptBlock

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 内容块稳定 ID |
| scene_id | string | 所属场次 ID |
| block_type | action / dialogue / voiceover / transition | 内容类型 |
| character_snapshot_id | string \| null | 对白关联项目角色 |
| temporary_speaker_name | string \| null | 临时人物名称 |
| content | string | 正文 |
| emotion | string \| null | 情绪提示 |
| performance_note | string \| null | 表演或语气提示 |
| sort_order | integer | 服务端规范化排序值 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.4 EpisodeScriptSavePayload

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| revision | integer \| null | 是 | 新建时为 `null`，更新时为当前修订号 |
| title | string \| null | 否 | 最长 120 字 |
| manual_duration_seconds | number \| null | 否 | 人工总时长 |
| scenes | ScriptScenePayload[] | 是 | 完整有序场次数组 |

`ScriptScenePayload`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | string \| null | 是 | 新建为 `null`；已有场次必须回传稳定 ID |
| title | string \| null | 否 | 最长 120 字 |
| location | string \| null | 否 | 草稿保存可空，确认必填，最长 120 字 |
| time_of_day | enum \| null | 否 | 草稿保存可空，确认必填 |
| interior_exterior | enum \| null | 否 | 草稿保存可空，确认必填 |
| character_snapshot_ids | string[] | 是 | 去重后的当前项目角色快照 ID |
| manual_duration_seconds | number \| null | 否 | 人工场次时长 |
| story_purpose | string \| null | 否 | 最长 1000 字 |
| blocks | ScriptBlockPayload[] | 是 | 完整有序块数组 |

`ScriptBlockPayload`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | string \| null | 是 | 新建为 `null`；已有块必须回传稳定 ID |
| block_type | enum | 是 | 四种合法类型之一 |
| character_snapshot_id | string \| null | 否 | 仅对白有效 |
| temporary_speaker_name | string \| null | 否 | 仅对白有效，最长 120 字 |
| content | string \| null | 否 | 草稿保存可空，确认非空，最长 10000 字 |
| emotion | string \| null | 否 | 最长 120 字 |
| performance_note | string \| null | 否 | 最长 1000 字 |

保存草稿允许不完整场次和空块，以支持编辑过程；服务端必须返回 `validation_issues`，但只有字段超长、枚举非法、跨项目引用、ID 归属错误和数量上限等合同错误返回 `422`。提交和确认时所有结构错误均阻止操作。

数量上限：每个剧本最多 200 个场次，每场最多 500 个内容块。

### 3.5 EpisodeScriptVersion

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 历史版本 ID |
| script_id | string | 正式剧本 ID |
| version | integer | 正式版本号 |
| source_content_version | string \| null | 来源正文版本 |
| snapshot | object | 当时完整规范化聚合快照 |
| change_source | manual_save / generation_adopt / migration | 版本来源 |
| generation_id | string \| null | 采用候选时的生成记录 |
| created_at | datetime | 版本创建时间 |

正式版本不可更新或删除。

### 3.6 ScriptGeneration

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 生成记录 ID |
| project_id | string | 项目 ID |
| episode_no | integer | 集数 |
| generation_scope | episode / scene / blocks | 生成范围 |
| target_scene_id | string \| null | 场次目标 |
| target_block_ids | string[] | 块目标 |
| rewrite_preset | enum \| null | 预设方向 |
| instruction | string \| null | 自定义指令 |
| base_script_version | integer \| null | 生成时正式版本 |
| base_script_revision | integer \| null | 生成时修订号 |
| input_snapshot | object | 完整输入快照 |
| output_snapshot | object | 结构化候选输出 |
| status | candidate / adopted / discarded | 状态 |
| client_request_id | string | 幂等请求标识 |
| model_config_id | string \| null | 模型配置 ID |
| model_name | string \| null | 实际模型名称 |
| elapsed_ms | integer \| null | 生成耗时 |
| adopted_at | datetime \| null | 采用时间 |
| created_at | datetime | 创建时间 |

候选列表响应默认不返回完整 `input_snapshot` 和 `output_snapshot`，详情接口才返回，避免列表载荷过大。

### 3.7 ScriptGenerationCreatePayload

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| generation_scope | episode / scene / blocks | 是 | 生成范围 |
| target_scene_id | string \| null | 条件必填 | `scene`、`blocks` 必填 |
| target_block_ids | string[] | 条件必填 | `blocks` 必填 |
| rewrite_preset | enum \| null | 否 | 预设方向 |
| instruction | string \| null | 否 | 最长 2000 字 |
| client_request_id | string | 是 | 最长 80 字 |
| base_script_version | integer \| null | 是 | 无正式稿整集生成时为 `null` |
| base_script_revision | integer \| null | 是 | 无正式稿整集生成时为 `null` |

`rewrite_preset` 允许：`more_satisfying`、`more_tragic`、`more_suspenseful`、`more_colloquial`、`short_video_pacing`、`compress_duration`、`stronger_cliffhanger`。

### 3.8 ScriptCheckResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 检查记录 ID |
| script_id | string | 剧本 ID |
| script_version | integer | 检查基于的正式版本 |
| script_revision | integer | 检查基于的修订号 |
| mode | structure / full | 检查模式 |
| semantic_check_status | not_requested / succeeded / failed | 语义检查状态 |
| issues | ScriptCheckIssue[] | 检查项 |
| model_config_id | string \| null | 完整检查使用的模型配置 |
| model_name | string \| null | 实际模型名称 |
| created_at | datetime | 检查时间 |

`ScriptCheckIssue` 包含：`code`、`severity`、`message`、`scene_id`、`block_id`、`details`。`severity` 只允许 `error`、`warning`、`info`。

## 4. 接口定义

### 4.1 查询正式剧本

```text
GET /api/projects/{project_id}/episode-scripts/{episode_no}
```

响应：

- `200`：`EpisodeScript | null`。
- `400`：集数非法。
- `404`：项目不存在。

不存在时返回 `null`，不得在读取时创建空聚合。

### 4.2 原子保存完整聚合

```text
PUT /api/projects/{project_id}/episode-scripts/{episode_no}
```

请求体：`EpisodeScriptSavePayload`。

响应：

- `200`：规范化后的 `EpisodeScript`。
- `400`：项目或集数业务校验失败。
- `409`：`revision` 不一致。
- `422`：合同字段、ID 归属、角色引用或数量上限错误。

业务要求：

- 新建时允许 `revision = null`；已有聚合时 `null` 返回 `409`。
- 保留客户端回传且归属正确的稳定 ID；为 `null` 的新节点由服务端生成 ID。
- 服务端按数组顺序规范化排序、估算时长并返回结构问题。
- 被请求数组移除的已有场次和块在事务内删除；历史版本快照仍保留。
- 实质变化写入新正式版本并传播下游；无实质变化不得制造空版本。

### 4.3 创建候选

```text
POST /api/projects/{project_id}/episode-scripts/{episode_no}/generations
```

请求体：`ScriptGenerationCreatePayload`。

响应：

- `201`：`ScriptGeneration`。
- `200`：同一幂等请求已存在时返回原记录。
- `400`：缺少正文、模型配置、目标或指令非法。
- `404`：项目、正式剧本、场次或内容块不存在。
- `409`：基准版本已经变化。
- `422`：模型输出无法通过结构 schema 校验。

同步实现应设置合理超时；后续改为异步任务时需保持最终对象和幂等语义不变。

### 4.4 查询候选列表

```text
GET /api/projects/{project_id}/episode-scripts/{episode_no}/generations?status=candidate&limit=20&cursor=...
```

- `status` 可选。
- `limit` 默认 20，最大 100。
- 按 `created_at desc` 返回摘要和下一页游标。

### 4.5 查询候选详情

```text
GET /api/projects/{project_id}/episode-scripts/{episode_no}/generations/{generation_id}
```

响应完整输入和输出快照；候选不存在或不属于当前集返回 `404`。

### 4.6 采用候选

```text
POST /api/projects/{project_id}/episode-scripts/{episode_no}/generations/{generation_id}/adopt
```

请求体：

```json
{
  "revision": 7
}
```

`revision` 类型为 `integer | null`；候选生成时尚无正式稿的整集候选采用传 `null`。

响应：

```json
{
  "generation": {},
  "script": {}
}
```

- `200`：采用成功或重复采用后的幂等结果。
- `404`：候选不存在。
- `409`：候选已放弃、正式版本变化或目标范围变化。
- `422`：候选内容不再满足结构合同。

### 4.7 放弃候选

```text
POST /api/projects/{project_id}/episode-scripts/{episode_no}/generations/{generation_id}/discard
```

- `200`：更新后的候选记录。
- 对已放弃候选重复调用幂等返回。
- 已采用候选返回 `409`，不得改为放弃。

### 4.8 执行一致性检查

```text
POST /api/projects/{project_id}/episode-scripts/{episode_no}/checks
```

请求体：

```json
{
  "revision": 7,
  "mode": "full"
}
```

响应 `ScriptCheckResult`。`revision` 冲突返回 `409`；`full` 缺少模型配置时返回结构结果，并令 `semantic_check_status = failed`，同时附带可重试提示。

### 4.9 提交待确认

```text
POST /api/projects/{project_id}/episode-scripts/{episode_no}/submit-review
```

请求体：`{ "revision": 7 }`。

- 服务端重新执行结构检查。
- 存在 `error` 返回 `422` 和完整问题列表。
- 成功后状态为 `pending_review`，`revision` 递增，`version` 不变。

### 4.10 确认剧本

```text
POST /api/projects/{project_id}/episode-scripts/{episode_no}/confirm
```

请求体：`{ "revision": 8 }`。

- 服务端重新执行结构检查，不信任客户端旧结果。
- 存在 `error` 返回 `422`。
- `warning` 不阻止确认。
- 成功后状态为 `confirmed`，设置 `confirmed_at`，`revision` 递增，`version` 不变。

### 4.11 查询正式版本列表

```text
GET /api/projects/{project_id}/episode-scripts/{episode_no}/versions?limit=20&cursor=...
```

返回版本号、来源正文版本、变更来源、生成记录 ID、时长、场次数和创建时间，不默认返回完整快照。

### 4.12 查询正式版本详情

```text
GET /api/projects/{project_id}/episode-scripts/{episode_no}/versions/{version}
```

返回不可变 `EpisodeScriptVersion` 完整快照。第一版只读，不提供回滚接口；用户如需恢复，可在后续版本通过“基于历史创建候选”实现。

## 5. 数据库与迁移

### 5.1 目标表

建议目标表：

- `project_episode_scripts`：聚合根当前状态。
- `project_script_scenes`：当前正式场次。
- `project_script_blocks`：当前正式内容块。
- `project_episode_script_versions`：不可变正式版本快照。
- `project_script_generations`：候选生成记录。
- `project_script_check_runs`：检查记录。

必要约束：

- `project_episode_scripts(project_id, episode_no)` 唯一。
- `project_script_scenes(script_id, sort_order)` 唯一。
- `project_script_blocks(scene_id, sort_order)` 唯一。
- `project_episode_script_versions(script_id, version)` 唯一。
- `project_script_generations(project_id, episode_no, generation_scope, client_request_id)` 唯一。
- 所有子表外键使用明确级联策略；删除项目时可级联，业务层不得删除正式历史。

### 5.2 旧四字段迁移

对每条现有 `project_episode_scripts` 执行幂等迁移：

1. 增加新聚合字段，保留原 `id`、`project_id`、`episode_no`、时间戳和状态。
2. 创建标题“待整理场次”的场次。
3. 从 `scene_text` 提取地点只允许使用确定性、无损规则；无法确定时地点使用“待整理地点”，并把完整原文创建为动作块。
4. 按固定顺序迁移非空字段：`scene_text` 附加动作块、`action_notes` 动作块、`dialogue` 对白块、`voiceover` 旁白块。
5. 对无法可靠识别说话人的旧对白，使用临时人物名称“待整理人物”，完整保留原文。
6. 不拆分或重排旧字段内部文本，确保每个非空字符都出现在迁移结果或迁移来源快照中。
7. 设置 `revision = 1`、`version = 1`、状态 `needs_review`，计算时长并写入 `migration` 正式版本。
8. 在正式版本快照的迁移元数据中保存四个旧字段原值和迁移规则版本。
9. 无任何非空旧字段的记录迁移为空场次草稿，或保留无场次聚合；不得伪造有效内容。

迁移任务以原剧本 ID 为幂等键。重复执行不得重复创建场次、块或历史版本。

### 5.3 兼容窗口

- 数据库迁移第一阶段保留旧四字段列，只读用于核对，不再由新接口写入。
- 新接口只返回结构化对象，不同时维护双写字段，避免顺序信息丢失。
- 完成数据核验和前端切换后，另行迁移删除旧列。
- 回滚应用版本时必须能读取保留列；因此删除旧列不得与首次结构迁移放在同一个发布步骤。

## 6. 错误合同

错误响应统一包含：

```json
{
  "code": "script_revision_conflict",
  "message": "剧本已在其他操作中更新",
  "details": {},
  "issues": []
}
```

| HTTP | code | 场景 |
| --- | --- | --- |
| 400 | `episode_out_of_range` | 集数超出项目范围 |
| 400 | `episode_content_required` | 整集生成缺少正文 |
| 400 | `text_model_required` | 缺少可用文本模型配置 |
| 404 | `project_not_found` | 项目不存在 |
| 404 | `script_not_found` | 正式剧本不存在 |
| 404 | `script_generation_not_found` | 候选不存在 |
| 409 | `script_revision_conflict` | 保存或状态操作修订冲突 |
| 409 | `generation_base_changed` | 候选基准或目标已变化 |
| 409 | `generation_not_adoptable` | 候选已放弃或状态非法 |
| 422 | `script_validation_failed` | 字段、结构或确认门槛失败 |
| 422 | `generation_output_invalid` | 模型输出不符合结构 schema |

`issues` 用于可定位的场次和内容块问题；内部异常、模型原始响应和密钥不得返回客户端。

## 7. 测试要求

### 7.1 聚合与并发

- 新建、读取和原子保存完整聚合。
- 场次和块新增、编辑、删除、复制结果及排序规范化。
- 空白规范化后无实质变化不增加 `version`。
- 展示字段只增加 `revision`，不传播下游。
- 实质变化增加正式版本并传播下游。
- 过期 `revision` 保存、采用、提交和确认均返回 `409`。
- 任一子节点校验失败时无部分写入。

### 7.2 校验与状态

- 场次必填、空块、对白说话人、角色项目隔离和数量上限。
- 草稿允许不完整结构，提交和确认被结构错误阻止。
- 警告不阻止保存或确认。
- 确认后实质编辑或采用候选回到草稿。
- 上游变化标记 `needs_review`，不覆盖内容。

### 7.3 生成与采用

- 三种范围生成的输入快照完整性。
- 幂等请求只调用模型一次。
- 无效模型输出不创建可采用候选。
- 整集采用只替换整集；场次和块采用严格限制范围。
- 候选生成后正式内容变化时采用冲突。
- 重复采用幂等，已放弃候选不可采用。
- 未采用候选上限 20 条，已采用候选不清理。

### 7.4 时长与检查

- 四类块默认估算、最小时长和小数舍入。
- 场次与整集人工覆盖优先级。
- 10% 和 25% 阈值边界。
- 结构与完整检查结果分级、定位和基准版本。
- 语义模型失败仍返回结构结果且不修改正式内容。

### 7.5 迁移

- 四个旧字段各种空值组合。
- 所有非空文本无损保留。
- 无法识别说话人使用“待整理人物”。
- 迁移后状态为 `needs_review` 并存在版本 1。
- 重复执行迁移不产生重复数据。

## 8. 验收标准

- 正式剧本由有序场次和有序内容块组成，服务端统一维护排序。
- 保存完整聚合是原子操作，并使用 `revision` 防止静默覆盖。
- 正式 `version` 只随实质内容变化递增，历史版本永久保留。
- 整集、场次和块生成均先创建持久化候选，采用前正式内容不变。
- 局部采用不改变范围外稳定 ID、内容和顺序。
- 自动时长、人工覆盖、最终时长和目标偏差按统一服务计算。
- 结构错误阻止提交和确认；警告和信息不阻止。
- 剧本实质变化正确标记同集下游为 `needs_review`。
- 每集最多保留 20 条未采用候选，已采用候选和正式版本不被清理。
- 旧四字段剧本迁移无文本丢失、可重复执行并标记为 `needs_review`。
- 接口不会修改世界观、角色、故事大纲、分集大纲或故事正文。

## 9. 关联文档

- [结构化剧本模块 PRD](../module-prds/production/structured-script.md)
- [结构化剧本前端 Spec](../frontend-specs/structured-script.md)
- [外部 AI 视频工具制作包](../module-prds/production/external-ai-production-package.md)
- [分镜制作 PRD](../module-prds/production/storyboard-production.md)
- [分集大纲与单集故事正文后端 Spec](./episode-outline.md)
- [项目工作台后端 Spec](./project-workbench.md)
