# 前端页面 Spec：Skill 管理

## 1. 页面信息

- 页面名称：Skill 管理
- 路由：`/skills`
- 页面类型：平台配置 / 全局能力管理
- 关联 PRD：[用户侧 Skill 管理](../module-prds/platform/user-skill-management.md)
- 后端接口 Spec：[用户侧 Skill 管理](../backend-specs/user-skill-management.md)

## 2. 页面目标

让用户在一个独立页面中查看当前工作台可用的用户侧业务 Skill，并切换某个 Skill 是否启用。

页面不承担 Skill 内容编辑、安装、卸载或版本管理。

## 3. 信息架构

页面包含：

- 页面标题：Skill 管理。
- 页面说明：说明禁用后会停止依赖该 Skill 的 AI 生成能力，但不影响已保存内容和手动编辑。
- 状态提示区：
  - 切换成功提示。
  - 加载或提交失败提示。
- 用户侧业务 Skill 列表。

列表项展示：

- Skill 名称。
- 启用状态 Badge：已启用 / 已禁用。
- Skill 描述。
- 来源目录。
- 更新时间。
- 操作按钮：启用 / 禁用。

## 4. 交互规则

- 页面进入后自动请求 Skill 列表。
- 加载中展示 Skeleton。
- 列表为空时展示空状态。
- 点击“禁用”后提交 `enabled=false`。
- 点击“启用”后提交 `enabled=true`。
- 提交中当前按钮禁用并显示“处理中...”。
- 切换成功后，页面就地更新该列表项，不要求整页刷新。
- 切换失败时，保留原状态并展示错误信息。

## 5. 状态设计

| 状态 | 页面表现 |
| --- | --- |
| 初始加载 | 展示列表 Skeleton |
| 加载成功且有数据 | 展示 Skill 列表 |
| 加载成功但无数据 | 展示“当前没有可管理的用户侧业务 Skill。” |
| 加载失败 | 展示错误信息 |
| 切换中 | 当前按钮禁用，文案为“处理中...” |
| 切换成功 | 更新 Badge 和按钮文案，展示成功提示 |
| 切换失败 | 展示错误信息，不改变原列表状态 |

## 6. API 依赖

接口合同以后端接口 Spec 为准；本节只描述页面调用关系。

| 行为 | 前端方法 | 后端接口 | 请求数据 | 响应数据 | 错误处理 |
| --- | --- | --- | --- | --- | --- |
| 加载 Skill 列表 | `listUserSkills()` | `GET /api/skills` | 无 | `UserSkill[]` | 页面展示错误信息 |
| 切换 Skill 开关 | `updateUserSkill(skillName, { enabled })` | `PATCH /api/skills/{skill_name}` | `enabled` | `UserSkill` | 保留原状态并展示错误信息 |

## 7. 布局要求

- 使用现有工作台页面结构：`stack`、`page-header`、`panel`。
- 列表项复用现有 `asset-card` 风格。
- 状态使用现有 `Badge` 组件和 `status-badge` 样式。
- 操作使用 shadcn/ui `Button`。
- 加载态使用 shadcn/ui `Skeleton`。
- 不新增复杂表单，不使用弹窗作为默认交互。
- 第一期默认面向桌面端，不要求移动端专门适配。

## 8. 文案

页面说明：

```text
管理项目内用户侧业务 Skill。禁用后，依赖该 Skill 的 AI 生成能力会停止调用，但不会影响已保存内容和手动编辑。
```

空状态：

```text
当前没有可管理的用户侧业务 Skill。
```

成功提示：

```text
{skill_name} 已启用。
{skill_name} 已禁用。
```

## 9. 验收标准

- 左侧导航存在“Skill 管理”入口。
- 用户点击入口后进入 `/skills`。
- 页面可以展示 `short-drama-creator`。
- 默认启用状态显示为“已启用”。
- 点击“禁用”后状态变为“已禁用”。
- 点击“启用”后状态变为“已启用”。
- 切换失败时展示错误信息。
- `npm --prefix apps/web run typecheck` 通过。

## 10. 非目标

- 不支持 Skill 内容编辑。
- 不支持 Skill 安装、卸载、上传或重新扫描按钮。
- 不支持按项目配置 Skill。
- 不支持运行时 Skill 管理。
