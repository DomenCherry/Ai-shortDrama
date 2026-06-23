# 后端接口 Spec：用户侧 Skill 管理

## 1. 适用范围

本文档定义用户侧业务 Skill 管理的后端接口合同、数据库写入边界和生成任务前置校验规则。

覆盖能力：

- 扫描 `skills/*/SKILL.md`。
- 合并数据库中的全局启用状态。
- 查询用户侧业务 Skill 列表。
- 切换单个用户侧业务 Skill 启用状态。
- 在依赖业务 Skill 的 AI 生成入口执行强校验。

不覆盖能力：

- Skill 安装、卸载和编辑。
- 开发辅助 Skill 管理。
- `runtime-skills/` 管理。
- 多用户权限、团队策略和审计日志。

## 2. 核心后端规则

### 2.1 Skill 发现规则

- 只扫描仓库根目录下 `skills/*/SKILL.md`。
- 不扫描 `.local-skills/`。
- 不扫描 `runtime-skills/`。
- `name` 优先读取 `SKILL.md` frontmatter；缺失时使用 Skill 目录名。
- `description` 读取 `SKILL.md` frontmatter；缺失时返回空字符串。
- `source_dir` 返回相对目录，例如 `skills/short-drama-creator`。

### 2.2 默认启用规则

- 如果数据库没有对应 `user_skill_settings` 记录，Skill 视为 `enabled=true`。
- 只有用户切换过开关后，才写入 `user_skill_settings`。
- 列表接口需要同时返回默认启用和已写入设置的 Skill。

### 2.3 生成任务前置校验

后端必须提供统一校验能力：

```text
ensure_user_skill_enabled(skill_name)
```

当 `enabled=false` 时：

- 直接抛出业务错误。
- 不读取模型配置。
- 不调用外部文本模型。
- 不创建生成候选记录。

禁用 `short-drama-creator` 时必须阻断：

- 故事大纲生成。
- 故事大纲局部改写。
- 故事大纲 AI 协助。
- 参考故事结构抽取。
- 单集故事正文生成、续写、润色。
- 结构化剧本生成和改写。
- 分镜场次生成。

禁用 Skill 不阻断手动保存、读取、候选采用、候选放弃和模型配置管理。

## 3. 数据对象

### 3.1 user_skill_settings

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| skill_name | varchar(120) | primary key | Skill 标识 |
| enabled | boolean | not null, default true | 是否启用 |
| created_at | timestamptz | not null | 创建时间 |
| updated_at | timestamptz | not null | 更新时间 |

### 3.2 UserSkillResponse

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| name | string | Skill 标识 |
| description | string | Skill 描述 |
| source_dir | string | Skill 来源目录 |
| enabled | boolean | 是否启用 |
| updated_at | string \| null | 开关状态更新时间；默认启用且未写入设置时为空 |

### 3.3 UserSkillUpdate

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| enabled | boolean | 是 | 目标启用状态 |

## 4. 接口定义

### 4.1 查询用户侧业务 Skill 列表

```text
GET /api/skills
```

响应：

- `200`：`UserSkillResponse[]`。

业务要求：

- 按 Skill 来源目录稳定排序。
- 仓库没有 `skills/` 目录时返回空数组。
- 不返回开发辅助 Skill 和运行时 Skill。
- 不返回 Skill 文件完整内容。

示例响应：

```json
[
  {
    "name": "short-drama-creator",
    "description": "当需要帮助用户创建 AI 短剧项目时使用，包括选题策划、整体故事大纲、人物设定、人物示意图提示词、分集大纲、单集剧本，以及可用于短剧制作的文本资料。具体创作质量规则参考 rules/ 下的短剧创作规则。",
    "source_dir": "skills/short-drama-creator",
    "enabled": true,
    "updated_at": null
  }
]
```

### 4.2 更新用户侧业务 Skill 开关

```text
PATCH /api/skills/{skill_name}
```

请求体：

```json
{
  "enabled": false
}
```

响应：

- `200`：更新后的 `UserSkillResponse`。
- `404`：Skill 不存在。

业务要求：

- 后端必须先确认 `skill_name` 对应的 Skill 文件存在。
- 首次更新时创建 `user_skill_settings`。
- 后续更新时只修改 `enabled` 和 `updated_at`。
- 不允许通过该接口创建仓库中不存在的 Skill。

## 5. 错误规则

| 场景 | HTTP 状态 | detail |
| --- | --- | --- |
| 更新不存在的 Skill | 404 | Skill 不存在 |
| 调用禁用 Skill 依赖的生成入口 | 400 | `{skill_name} skill 已禁用，请在 Skill 管理中启用后再使用生成能力。` |

生成入口的禁用错误属于业务前置条件不满足，使用 `400`。

## 6. 数据迁移

新增 Alembic migration：

```text
apps/api/alembic/versions/0016_user_skill_settings.py
```

迁移内容：

- 创建 `user_skill_settings` 表。
- 不预置任何记录；默认启用规则由 service 层合并实现。

## 7. 前端 Service 对齐

| 前端方法 | 后端接口 | 说明 |
| --- | --- | --- |
| `listUserSkills()` | `GET /api/skills` | 读取 Skill 列表 |
| `updateUserSkill(skillName, payload)` | `PATCH /api/skills/{skill_name}` | 切换 Skill 开关 |

## 8. 测试要求

- `GET /api/skills` 能发现 `skills/short-drama-creator/SKILL.md`。
- 未写入数据库设置时，列表返回 `enabled=true`。
- `PATCH /api/skills/short-drama-creator` 能持久化启用状态。
- 禁用 `short-drama-creator` 后，依赖该 Skill 的生成入口在模型调用前返回错误。
- 禁用 `short-drama-creator` 后，手动保存接口不受影响。
