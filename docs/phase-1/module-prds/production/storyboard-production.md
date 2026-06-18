# 模块 PRD：分镜制作

> 状态：**模块边界已确认，待详细设计**

## 1. 问题陈述

结构化剧本不能直接作为 AI 图片或视频工具的生产输入。创作者需要把场次拆成镜头，并为每个镜头维护画面、动作、声音、时长和外部生成提示词。

## 2. 解决方案

按场次生成和维护镜头列表。AI 素材提示词作为镜头内部内容保存，确保提示词与镜头画面、人物、动作和时长一致。

## 3. 输入与输出

输入：已保存的结构化剧本、项目角色与场景参考、项目视觉风格。

输出：

- 按场次分组的镜头列表。
- 镜头级画面、声音、时长和连续性信息。
- 图片、视频和负面提示词。
- 首帧、尾帧及外部工具生成参数。
- 可供后期准备和制作包导出的正式分镜版本。

## 4. 功能范围

- 从结构化剧本生成候选分镜。
- 新增、复制、编辑、删除和排序镜头。
- 在场次内或跨场次调整镜头。
- 重新生成单个镜头。
- 生成和编辑镜头 AI 素材提示词。
- 引用人物和场景一致性素材。
- 统计场次和整集镜头时长。
- 检查对白覆盖、人物连续性和镜头衔接。

## 5. 初步数据对象

### 5.1 Storyboard

- id
- project_id
- episode_no
- source_script_version
- status
- total_duration_seconds
- created_at
- updated_at

### 5.2 StoryboardShot

- id
- storyboard_id
- scene_id
- shot_no
- shot_size
- camera_angle
- camera_movement
- composition
- character_snapshot_ids
- action
- expression
- environment
- props
- visual_description
- duration_seconds
- dialogue
- voiceover
- sound_effect
- music_note
- continuity_note
- sort_order
- status

### 5.3 ShotGenerationPrompt

- id
- shot_id
- image_prompt
- video_prompt
- negative_prompt
- first_frame_description
- last_frame_description
- reference_asset_ids
- aspect_ratio
- duration_seconds
- style_parameters
- adapter_parameters

字段和平台适配参数仍需单独细化。

## 6. Seedance 适配原则

- 核心镜头字段保持平台无关。
- Seedance 专用字段保存在适配结果或导出配置中。
- 在 Seedance 能力和接口确认前，不把其临时参数提升为核心数据字段。
- 第一版优先保证视频提示词、首尾帧、参考素材、画幅和时长可以完整导出。

## 7. 状态与依赖

- 剧本变化后，分镜标记为需要检查。
- 分镜实质变化后，后期准备和制作包标记为需要检查。
- 单个镜头重新生成不能修改其他镜头。
- 删除场次时，其关联镜头必须进入明确的处理流程，不能成为孤立数据。

## 8. 用户故事

1. 作为短剧创作者，我想从剧本自动拆分镜头，以便快速获得制作清单。
2. 作为短剧创作者，我想逐镜头编辑画面和时长，以便控制视频节奏。
3. 作为 AI 视频创作者，我想为每个镜头获得视频提示词，以便交给外部工具生成素材。
4. 作为 AI 视频创作者，我想引用已确认人物和场景素材，以便保持视觉一致性。
5. 作为短剧创作者，我想只重新生成一个镜头，以便保留其他人工调整。
6. 作为剪辑人员，我想看到镜头顺序和声音信息，以便准备后期工作。

## 9. 验收标准

- 系统可以从结构化剧本生成按场次分组的候选分镜。
- 每个镜头能追溯到所属场次和剧本版本。
- 用户可以新增、编辑、复制、删除和排序镜头。
- 每个镜头可以维护图片、视频和负面提示词。
- 单镜头重新生成不影响其他镜头。
- 系统显示场次和整集分镜时长。
- 分镜变化后正确传播下游状态。

## 10. 测试决策

- 重点测试剧本到镜头的追溯、镜头排序、局部重新生成和状态传播。
- 检查时长计算、孤立镜头防护和提示词导出完整性。
- 外部工具适配测试只验证转换合同，不依赖真实视频生成结果。

## 11. 非目标

- 不在本模块生成完整视频成片。
- 不提供时间线剪辑器。
- 不保证 Seedance 生成结果质量。
- 不维护最终字幕时间轴。

## 12. 待细化问题

- 镜头字段、枚举和必填规则。
- 场次拆镜头的生成策略。
- 提示词结构和人物一致性引用方式。
- Seedance 适配输出格式。
- 分镜表格与镜头详情的交互结构。

## 13. 关联文档

- [制作包总览](./external-ai-production-package.md)
- [结构化剧本](./structured-script.md)
- [后期准备](./post-production-prep.md)

