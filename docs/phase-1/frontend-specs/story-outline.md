# 前端页面 Spec：项目故事大纲

## 1. 页面目标

- 工作台路径：`/projects/[id]?stage=story`
- AI 提取路径：`/projects/[id]/story-outline/extract`
- 所属阶段：项目工作台 `故事大纲` tab。
- 目标：让用户在工作台内手动维护正式故事大纲，并通过独立 AI 提取页上传或粘贴参考故事，抽取去具体化的故事大纲预览，人工调整后确认写入正式故事大纲。

本 spec 描述项目工作台故事大纲阶段的复杂交互。项目工作台整体导航、基础信息、资产快照、分集、剧本、分镜和文案仍以 [项目工作台页面 Spec](./project-workbench.md) 为准。

## 2. 信息架构

故事大纲阶段包含：

- 正式故事大纲编辑区。
- 【AI提取】跳转入口。
- AI 提取页的参考故事输入区。
- AI 提取页的可编辑故事大纲预览区。
- 校验状态与保存反馈区。

### 2.1 正式故事大纲编辑区

字段按三层分组展示：

- 故事核心层：一句话故事、故事背景、主线目标、核心矛盾、故事起点、结局方向。
- 结构规划层：起承转合结构、阶段性反转、情绪曲线、关键伏笔、人物弧光。
- 执行辅助层：整体节奏建议、剧情容量建议、补充说明、状态。

展示规则：

- 每个分组显示短标题和一句说明。
- 每个文本字段使用输入框 `placeholder` 展示字段作用和填写案例。
- 用户输入内容后，placeholder 自动消失。
- 不默认展开大段字段说明，不使用 hover 作为唯一说明方式。
- 故事大纲只承载全剧级骨架，不展示分集剧情、单集故事正文或短剧脚本字段。

操作：

- 保存正式大纲。
- 跳转到 AI 提取页。
- 将状态切换为草稿、已确认或需要检查。

### 2.2 AI 提取入口

- 工作台故事大纲 tab 顶部展示【AI提取】按钮。
- 点击后跳转到 `/projects/{project_id}/story-outline/extract`。
- 跳转不保存当前未提交的工作台表单内容。

### 2.3 AI 提取页输入区

输入方式：

- 粘贴参考故事文本。
- 上传 `.txt` / `.md` 文本文件。

字段：

- 参考文本输入框。
- 文件选择控件。
- 文件名预览。
- 用户补充抽取要求。

操作：

- 开始提取。
- 清空参考输入。
- 返回故事大纲。

约束：

- 第一版只接受 `.txt` / `.md`。
- 参考故事输入只用于抽取结构，不直接进入正式故事大纲。
- 抽取时应展示“提取中...”状态。

### 2.4 AI 提取页故事大纲预览区

展示字段：

- 使用正式故事大纲的全部字段，并沿用正式编辑区的三层分组、字段 placeholder 和状态选择。
- 预览字段来自抽取接口返回的 `outline_preview`。
- 校验状态。
- 校验说明。

操作：

- 用户可以手动调整预览字段。
- 确认并返回工作台。
- 取消并返回工作台。

交互规则：

- `validation_status = "passed"` 的草稿才允许确认写入正式故事大纲。
- `validation_status = "failed"` 的草稿应展示失败原因，确认按钮禁用。
- 确认保存使用正式故事大纲保存接口。
- 保存成功后跳回 `/projects/{project_id}?stage=story`。

## 3. 页面状态

### 3.1 加载状态

- 项目加载中。
- 正式故事大纲加载中。
- AI 提取页项目资料加载中。
- 参考结构提取中。
- 正式故事大纲确认保存中。

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
| 去具体化校验失败 | 抽取结果未通过去具体化校验，不能确认写入正式故事大纲 |
| 确认保存失败 | 故事大纲确认失败 |

## 4. API 依赖

接口合同以后端接口 Spec 为准：[故事大纲后端 Spec](../backend-specs/story-outline.md)。

| 行为 | 前端方法 | 后端接口 | 请求数据 | 响应数据 | 错误处理 |
| --- | --- | --- | --- | --- | --- |
| 读取正式故事大纲 | `getProjectStoryOutline` | `GET /api/projects/{project_id}/story-outline` | project_id | `ProjectStoryOutline | null` | 展示大纲加载失败 |
| 保存正式故事大纲 | `updateProjectStoryOutline` | `PUT /api/projects/{project_id}/story-outline` | 正式大纲字段和状态 | `ProjectStoryOutline` | 保留表单内容，展示保存失败 |
| 抽取参考故事结构 | `extractReferenceStoryStructure` | `POST /api/projects/{project_id}/story-structure-drafts/extract` | `source_type`、`source_filename`、`source_text`、`user_requirements` | 带 `outline_preview` 的 `ReferenceStoryStructureDraft` | 展示抽取失败或校验失败 |

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

### 5.2 抽取参考故事结构

```text
用户在工作台故事大纲 tab 点击【AI提取】
 -> 跳转到 /projects/{project_id}/story-outline/extract
 -> 用户上传 txt/md 或粘贴参考故事
 -> 用户点击开始提取
 -> 前端调用结构抽取接口
 -> 后端使用独立结构抽取规则并执行去具体化校验
 -> 前端将 outline_preview 填充到故事大纲预览表单
 -> 用户可以手动调整预览字段
 -> 校验通过时允许确认保存正式故事大纲
 -> 校验失败时展示失败原因并禁用确认
```

### 5.3 确认 AI 提取结果

```text
用户查看并调整故事大纲预览
 -> 用户点击确认并返回工作台
 -> 前端调用正式故事大纲保存接口
 -> 保存成功后跳回 /projects/{project_id}?stage=story
 -> 工作台展示更新后的正式故事大纲
 -> 下游内容显示需要检查
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
- 预览字段：`outline_preview`，类型为 `ProjectStoryOutlinePayload`

## 7. 桌面端布局要求

- 第一期故事大纲页面默认面向桌面端使用，不要求移动端专门适配。
- 工作台故事大纲 tab 展示正式大纲编辑和【AI提取】入口。
- AI 提取页桌面端可以使用上下或左右布局：输入区与可编辑预览区都应完整展示。
- 预览字段较长时应自然换行，不允许文本溢出卡片或按钮。
- 文件上传区、文本输入区和操作按钮在桌面端应保持清晰可点击。

## 8. 验收标准

- 用户可以读取、编辑、保存正式故事大纲的完整字段。
- 保存正式故事大纲成功后，下游内容展示“需要检查”。
- 用户在工作台点击【AI提取】后进入独立 AI 提取页面。
- 用户可以上传 `.txt` / `.md` 或粘贴参考故事文本并触发结构抽取。
- 抽取完成后，`outline_preview` 按现有故事大纲字段填充到可编辑预览表单。
- 用户修改预览字段后点击确认，正式故事大纲刷新并返回工作台故事大纲 tab。
- 参考框架草稿校验通过时可以确认保存，校验失败时确认按钮禁用。
- 使用《西游记》相关故事作为输入时，前端展示的是旅程型使命结构等抽象内容，不展示具体角色、地点、任务名称或经典桥段。
- 仅上传或抽取预览不触发下游 `needs_review`；确认保存正式大纲后才触发。
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
