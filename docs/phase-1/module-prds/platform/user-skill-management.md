# 模块 PRD：用户侧 Skill 管理

## 1. 功能定位

用户侧 Skill 管理用于让创作者查看当前工作台可使用的业务 Skill，并全局控制某个业务 Skill 是否启用。

第一版只管理仓库 `skills/` 目录下的用户侧业务 Skill，不管理 `.local-skills/`、开发辅助 Skill 或 `runtime-skills/`。

## 2. 背景与问题

本项目把短剧创作能力沉淀为用户侧业务 Skill。随着后续继续拆分选题策划、故事大纲、人物设定、分集大纲、剧本生成和分镜拆解等 Skill，用户需要一个清晰入口理解当前有哪些业务能力，以及某个能力是否参与 AI 生成流程。

如果用户希望暂时关闭某个业务 Skill，系统不能只在页面上隐藏入口，而应在后端生成链路中真实阻断依赖该 Skill 的模型调用，避免用户误以为能力已关闭但后台仍继续使用。

## 3. 功能范围

第一期包括：

- 左侧导航新增“Skill 管理”入口。
- 展示 `skills/*/SKILL.md` 中声明的用户侧业务 Skill。
- 展示 Skill 名称、描述、来源目录、启用状态和最近更新时间。
- 支持全局启用 / 禁用单个用户侧业务 Skill。
- 禁用后，依赖该 Skill 的 AI 生成能力不得继续调用该 Skill 或发起对应模型生成。
- 未保存开关配置的 Skill 默认视为启用。

第一期不包括：

- 管理开发辅助 Skill。
- 管理 `runtime-skills/`。
- 按项目覆盖 Skill 开关。
- Skill 内容编辑、安装、卸载或版本管理。
- 多用户权限、团队级策略和审计日志。
- 前端本地偏好覆盖后端全局开关。

## 4. 数据对象

### 4.1 UserSkill

`UserSkill` 是前端展示对象，由仓库文件系统扫描结果和数据库开关合并得到。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | Skill 标识，优先读取 `SKILL.md` frontmatter 的 `name` |
| description | string | 否 | Skill 描述，读取 `SKILL.md` frontmatter 的 `description` |
| source_dir | string | 是 | 来源目录，例如 `skills/short-drama-creator` |
| enabled | boolean | 是 | 是否全局启用 |
| updated_at | datetime | 否 | 开关状态最近更新时间；默认启用且未写入配置时为空 |

### 4.2 UserSkillSetting

`UserSkillSetting` 保存用户侧业务 Skill 的全局开关。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| skill_name | string | 是 | Skill 标识，主键 |
| enabled | boolean | 是 | 是否启用 |
| created_at | datetime | 是 | 首次创建时间 |
| updated_at | datetime | 是 | 最近更新时间 |

## 5. 业务规则

- 系统只扫描 `skills/*/SKILL.md`。
- Skill 名称优先读取 frontmatter `name`；缺失时使用目录名。
- Skill 描述读取 frontmatter `description`；缺失时返回空字符串。
- 数据库中没有对应 `UserSkillSetting` 时，Skill 默认为启用。
- 更新开关时，如果 Skill 不存在，系统应返回“Skill 不存在”。
- 禁用 `short-drama-creator` 后，以下 AI 生成入口必须阻断：
  - 故事大纲生成。
  - 故事大纲局部改写。
  - 故事大纲 AI 协助。
  - 参考故事结构抽取。
  - 单集故事正文生成、续写、润色。
  - 结构化剧本生成和改写。
  - 分镜场次生成。
- 禁用 Skill 不影响：
  - 已保存内容查看。
  - 手动编辑和保存。
  - 候选稿查看、编辑、采用和放弃。
  - 模型 API 配置、测试和启用切换。
  - 项目、世界观、角色卡等基础数据管理。

## 6. 交互要求

- 用户从左侧导航进入“Skill 管理”。
- 页面默认加载用户侧业务 Skill 列表。
- 每个 Skill 以列表项展示，不使用复杂配置表单。
- Skill 状态用明确 Badge 展示：已启用 / 已禁用。
- 每个 Skill 提供一个主操作按钮：
  - 已启用时显示“禁用”。
  - 已禁用时显示“启用”。
- 切换中按钮进入禁用态，避免重复提交。
- 切换成功后页面展示简短状态反馈。
- 切换失败时展示后端错误信息。

## 7. 用户故事

1. 作为个人短剧创作者，我想看到当前工作台有哪些用户侧业务 Skill，以便理解系统当前可用的 AI 创作能力。
2. 作为个人短剧创作者，我想禁用某个用户侧业务 Skill，以便暂时停止使用该 Skill 驱动的生成能力。
3. 作为个人短剧创作者，我想重新启用某个用户侧业务 Skill，以便恢复对应生成能力。
4. 作为个人短剧创作者，我希望禁用后后端真正停止对应生成调用，而不是只隐藏页面入口。

## 8. 验收标准

- 进入“Skill 管理”后，可以看到 `skills/short-drama-creator/SKILL.md` 对应的 Skill。
- 默认未保存开关状态时，`short-drama-creator` 显示为已启用。
- 用户点击“禁用”后，页面状态更新为已禁用。
- 用户点击“启用”后，页面状态更新为已启用。
- 禁用 `short-drama-creator` 后，故事大纲生成等依赖该 Skill 的 AI 生成入口返回明确错误，不发起模型调用。
- 禁用 `short-drama-creator` 后，用户仍可手动编辑和保存已有故事大纲、正文、剧本、分镜和文案。
- 刷新页面后，Skill 开关状态保持不变。

## 9. 实现决策

- Skill 开关采用全局生效，不按项目区分。
- 后端是 Skill 是否可用的权威判断位置，前端仅展示状态和发起切换。
- 第一期只管理用户侧业务 Skill，运行时 Humanizer 类 Skill 不进入菜单，避免用户关闭底层质量处理能力后造成生成结果不可预期。

## 10. 后续扩展

- 支持按项目覆盖全局 Skill 默认值。
- 支持展示 Skill 版本、能力标签和依赖关系。
- 支持新增业务 Skill 后在菜单中分组展示。
- 支持禁用前展示影响范围确认。
- 支持记录 Skill 开关变更审计日志。

## 11. 关联文档

- 第一阶段 PRD：[prd.md](../../prd.md)
- 后端接口 Spec：[user-skill-management.md](../../backend-specs/user-skill-management.md)
- 前端页面 Spec：[user-skill-management.md](../../frontend-specs/user-skill-management.md)
- Skill 分层策略：[skills-strategy.md](../../../technical/skills-strategy.md)
