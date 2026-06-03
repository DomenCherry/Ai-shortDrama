# 前端页面 Spec：项目故事大纲

## 1. 页面目标

- 页面路径：`/projects/[id]`
- 所属阶段：项目工作台 `故事大纲` tab。
- 目标：让用户在项目内手动维护、AI 生成、局部改写整体故事大纲，并可上传或粘贴参考故事，抽取去具体化的参考框架草稿后选择应用到正式故事大纲。

本 spec 描述项目工作台故事大纲阶段的复杂交互。项目工作台整体导航、基础信息、资产快照、分集、剧本、分镜和文案仍以 [项目工作台页面 Spec](./project-workbench.md) 为准。

## 2. 信息架构

故事大纲阶段包含：

- 正式故事大纲编辑区。
- AI 生成与局部改写操作区。
- 参考故事结构抽取区。
- 参考框架草稿预览区。
- 上下文摘要与状态提示区。

### 2.1 正式故事大纲编辑区

字段：

- 一句话故事。
- 故事背景。
- 主线目标。
- 核心矛盾。
- 故事起点。
- 起承转合结构。
- 阶段性反转。
- 情绪曲线。
- 关键伏笔。
- 人物弧光。
- 结局方向。
- 整体节奏建议。
- 剧情容量建议。
- 补充说明。
- 状态：草稿、已确认、需要检查。

操作：

- 保存正式大纲。
- 还原到最近一次保存内容。
- 将状态切换为草稿、已确认或需要检查。

### 2.2 AI 生成与局部改写区

操作：

- 生成完整故事大纲。
- 预览生成结果。
- 应用生成结果到正式大纲。
- 对单个字段执行局部改写。
- 预览局部改写结果。
- 应用局部改写结果。

生成前应展示当前使用的上下文摘要，包括：

- 项目基础信息。
- 已加载世界观状态。
- 已加载角色数量。
- 是否使用参考框架草稿。

### 2.3 参考故事结构抽取区

输入方式：

- 粘贴参考故事文本。
- 上传 `.txt` / `.md` 文本文件。

字段：

- 参考文本输入框。
- 文件选择控件。
- 文件名预览。
- 用户补充抽取要求。

操作：

- 抽取参考结构。
- 清空参考输入。

约束：

- 第一版只接受 `.txt` / `.md`。
- 参考故事输入只用于抽取结构，不直接进入正式故事大纲。
- 抽取时应展示“正在抽取结构...”状态。

### 2.4 参考框架草稿预览区

展示字段：

- 故事类型。
- 主线目标模型。
- 起点事件类型。
- 核心冲突模型。
- 阶段结构。
- 反转机制。
- 情绪曲线。
- 伏笔与回收方式。
- 结局模式。
- 可迁移的短剧改编建议。
- 去具体化说明。
- 校验状态。
- 校验说明。

操作：

- 应用到正式大纲。
- 只填充空字段。
- 覆盖正式大纲相关字段。
- 废弃草稿。

交互规则：

- `validation_status = "passed"` 的草稿才允许应用。
- `validation_status = "failed"` 的草稿应展示失败原因，应用按钮禁用。
- 应用前如果正式大纲已有内容，应弹出确认提示。
- 应用成功后刷新正式故事大纲，并提示下游内容需要检查。

## 3. 页面状态

### 3.1 加载状态

- 项目加载中。
- 正式故事大纲加载中。
- 参考框架草稿列表加载中。
- 生成完整大纲中。
- 局部改写中。
- 参考结构抽取中。
- 应用参考框架中。

### 3.2 空状态

- 正式故事大纲为空：展示编辑入口、生成完整大纲入口和参考故事结构抽取入口。
- 无参考框架草稿：展示“暂无参考框架草稿”。
- 无文本模型配置：展示“请先配置并测试成功文本生成模型 API”，并提供前往设置页入口。

### 3.3 错误状态

| 场景 | 提示文案 |
| --- | --- |
| 项目不存在 | 项目不存在 |
| 故事大纲加载失败 | 整体故事大纲加载失败 |
| 故事大纲保存失败 | 整体故事大纲保存失败 |
| 文本模型不可用 | 请先配置并测试成功文本生成模型 API |
| 参考文本为空 | 请先上传或粘贴参考故事文本 |
| 文件类型非法 | 第一版只支持 txt 或 md 文本文件 |
| 抽取失败 | 参考故事结构抽取失败，请稍后重试 |
| 去具体化校验失败 | 抽取结果未通过去具体化校验，不能应用到正式故事大纲 |
| 应用失败 | 参考框架应用失败 |
| 局部改写失败 | 局部改写失败 |

## 4. API 依赖

接口合同以后端接口 Spec 为准：[故事大纲后端 Spec](../backend-specs/story-outline.md)。

| 行为 | 前端方法 | 后端接口 | 请求数据 | 响应数据 | 错误处理 |
| --- | --- | --- | --- | --- | --- |
| 读取正式故事大纲 | `getProjectStoryOutline` | `GET /api/projects/{project_id}/story-outline` | project_id | `ProjectStoryOutline | null` | 展示大纲加载失败 |
| 保存正式故事大纲 | `updateProjectStoryOutline` | `PUT /api/projects/{project_id}/story-outline` | 正式大纲字段和状态 | `ProjectStoryOutline` | 保留表单内容，展示保存失败 |
| 生成完整故事大纲 | `generateProjectStoryOutline` | `POST /api/projects/{project_id}/story-outline/generate` | `user_requirements`、`reference_draft_id`、`write_mode` | `StoryOutlineGenerationResult` | 展示生成失败或文本模型不可用 |
| 局部改写大纲字段 | `rewriteProjectStoryOutlineField` | `POST /api/projects/{project_id}/story-outline/rewrite` | `field`、`current_value`、`instruction`、`write_mode` | `StoryOutlineRewriteResult` | 展示局部改写失败 |
| 抽取参考故事结构 | `extractReferenceStoryStructure` | `POST /api/projects/{project_id}/story-structure-drafts/extract` | `source_type`、`source_filename`、`source_text`、`user_requirements` | `ReferenceStoryStructureDraft` | 展示抽取失败或校验失败 |
| 查询参考框架草稿 | `listReferenceStoryStructureDrafts` | `GET /api/projects/{project_id}/story-structure-drafts` | project_id | `ReferenceStoryStructureDraft[]` | 展示草稿加载失败 |
| 查询草稿详情 | `getReferenceStoryStructureDraft` | `GET /api/projects/{project_id}/story-structure-drafts/{draft_id}` | project_id、draft_id | `ReferenceStoryStructureDraft` | 展示草稿加载失败 |
| 应用参考框架草稿 | `applyReferenceStoryStructureDraft` | `POST /api/projects/{project_id}/story-structure-drafts/{draft_id}/apply` | `apply_mode`、`user_requirements` | `ProjectStoryOutline` | 展示应用失败 |
| 废弃参考框架草稿 | `discardReferenceStoryStructureDraft` | `POST /api/projects/{project_id}/story-structure-drafts/{draft_id}/discard` | project_id、draft_id | `ReferenceStoryStructureDraft` | 展示废弃失败 |

## 5. 交互流程

### 5.1 手动保存正式故事大纲

```text
用户进入故事大纲 tab
 -> 系统加载正式故事大纲
 -> 用户编辑字段
 -> 用户点击保存
 -> 前端调用保存接口
 -> 保存成功后刷新正式大纲
 -> 展示“整体故事大纲已保存，下游内容已标记为需要检查”
```

### 5.2 生成完整故事大纲并应用

```text
用户点击生成完整大纲
 -> 前端展示本次使用的上下文摘要
 -> 用户填写可选生成要求
 -> 系统调用 preview 生成接口
 -> 前端展示生成预览
 -> 用户点击应用
 -> 系统调用 apply 或保存接口写入正式大纲
 -> 正式大纲刷新，下游内容显示需要检查
```

### 5.3 局部改写字段

```text
用户在某个大纲字段旁点击局部改写
 -> 输入改写要求
 -> 系统调用局部改写 preview
 -> 前端展示改写前后内容
 -> 用户点击应用
 -> 系统写回该字段
 -> 正式大纲刷新，下游内容显示需要检查
```

### 5.4 抽取参考故事结构

```text
用户上传 txt/md 或粘贴参考故事
 -> 用户点击抽取参考结构
 -> 前端调用结构抽取接口
 -> 后端使用独立结构抽取规则并执行去具体化校验
 -> 前端展示参考框架草稿
 -> 校验通过时允许应用
 -> 校验失败时展示失败原因并禁用应用
```

### 5.5 应用参考框架草稿

```text
用户查看参考框架草稿
 -> 选择只填充空字段或覆盖相关字段
 -> 如果正式大纲已有内容，前端提示确认
 -> 用户确认应用
 -> 系统写入正式故事大纲
 -> 正式大纲刷新，下游内容显示需要检查
```

## 6. 前端类型建议

### 6.1 ProjectStoryOutlinePayload

应包含正式大纲全部可编辑字段：

- `logline`
- `story_background`
- `main_goal`
- `core_conflict`
- `story_start`
- `plot_structure`
- `reversals`
- `emotion_curve`
- `foreshadowing`
- `character_arcs`
- `ending_direction`
- `pacing_advice`
- `capacity_advice`
- `notes`
- `status`

### 6.2 ReferenceStoryStructureDraft

应包含：

- 来源字段：`source_type`、`source_filename`、`source_text_excerpt`
- 结构字段：`story_type`、`goal_model`、`inciting_event_type`、`conflict_model`、`stage_structure`、`reversal_mechanism`、`emotion_curve`、`foreshadowing_pattern`、`ending_pattern`、`adaptation_advice`
- 校验字段：`de_specificity_notes`、`validation_status`、`validation_notes`
- 状态字段：`status`、`created_at`、`updated_at`

## 7. 响应式要求

- 桌面端可以使用左右布局：左侧正式大纲编辑，右侧生成、抽取和草稿预览。
- 窄屏下必须改为单列布局，阶段导航和操作按钮不能横向撑破页面。
- 参考框架草稿字段较长时应自然换行，不允许文本溢出卡片或按钮。
- 文件上传区、文本输入区和操作按钮在移动宽度下保持可点击。

## 8. 验收标准

- 用户可以读取、编辑、保存正式故事大纲的完整字段。
- 保存正式故事大纲成功后，下游内容展示“需要检查”。
- 用户可以生成完整故事大纲预览，预览不会自动覆盖正式大纲。
- 用户确认后可以应用生成结果到正式大纲。
- 用户可以对单个大纲字段执行局部改写并应用。
- 用户可以上传 `.txt` / `.md` 或粘贴参考故事文本并触发结构抽取。
- 参考框架草稿校验通过时可以应用，校验失败时应用按钮禁用。
- 使用《西游记》相关故事作为输入时，前端展示的是旅程型使命结构等抽象内容，不展示具体角色、地点、任务名称或经典桥段。
- 应用参考框架草稿前，如果正式大纲已有内容，前端必须提示确认。
- 应用参考框架草稿后，正式故事大纲刷新，下游内容展示“需要检查”。
- 文本模型不可用时，生成、改写和抽取入口展示明确错误，并引导用户前往设置页。
- `npm --prefix apps/web run typecheck` 通过。

## 9. 非目标

- 不在第一版支持 PDF、Word、网页链接或图片 OCR。
- 不在前端做版权识别。
- 不自动将参考故事文本写入正式故事大纲。
- 不在故事大纲阶段实现分集大纲、人物设定或剧本生成。

## 10. 关联文档

- [故事大纲模块 PRD](../module-prds/story-outline.md)
- [故事大纲后端 Spec](../backend-specs/story-outline.md)
- [项目工作台页面 Spec](./project-workbench.md)
- [模型 API 配置前端 Spec](./model-api-settings.md)
