# 项目结构约定

## 1. 目标

本项目采用“应用代码、创作规则、运行产物分离”的结构。

目标是让 AI 短剧创作工具在早期保持简单，同时为后续故事生成、人物示意图、素材管理、导出和视频制作预留清晰边界。

## 2. 仓库结构

```text
.
├── apps
│   ├── api
│   └── web
├── docs
├── rules
├── skills
├── workspace
└── .local-skills
```

目录说明：

- `apps/api`：FastAPI 后端。
- `apps/web`：Next.js 前端。
- `docs`：产品、阶段、功能和技术文档。
- `rules`：用户侧短剧创作规则，需要同步到 GitHub。
- `skills`：用户侧业务 skill，需要同步到 GitHub。
- `workspace`：本地项目产物目录，具体运行产物不提交 GitHub。
- `.local-skills`：本地开发辅助 skill，不提交 GitHub。

## 3. 工作区策略

`workspace/projects/` 用于保存具体短剧项目的本地产物。

约定结构：

```text
workspace/projects/<project-id>
├── metadata.json
├── exports
├── assets
│   └── characters
├── generations
└── scripts
```

Git 策略：

- 提交 `workspace/README.md` 和 `workspace/projects/.gitkeep`。
- 忽略 `workspace/projects/*` 下的具体项目产物。
- 不把人物示意图、导出文件、生成历史和素材文件提交到 GitHub。

## 4. Rules 与 Skills 分工

用户侧创作能力分为两层：

- `skills/short-drama-creator/SKILL.md`：定义触发场景、核心流程和规则路由。
- `rules/*.md`：定义每个创作模块的产出结构、质量要求和检查点。

当前规则包括：

- 选题策划。
- 整体故事大纲。
- 人物设定。
- 人物示意图。
- 分集大纲。
- 单集剧本。

后续新增创作模块时，优先补充独立 rule，再更新 skill 路由。

## 5. 后端模块边界

当前后端保持：

```text
apps/api/app
├── api
├── core
├── models
└── services
```

约定：

- `api`：HTTP 路由和请求响应边界。
- `core`：配置、数据库连接和底层基础设施。
- `models`：SQLAlchemy 模型和 Pydantic schema。
- `services`：业务逻辑。

Projects 模块已按业务域拆分。对外 HTTP 路径保持 `/api/projects` 不变，内部结构为：

```text
apps/api/app
├── api
│   ├── projects.py
│   └── project_routes
│       ├── management.py
│       ├── assets.py
│       ├── story_outline.py
│       ├── episode_outlines.py
│       ├── episode_contents.py
│       ├── episode_scripts.py
│       └── production.py
└── services
    ├── projects.py
    └── project
        ├── common.py
        ├── management.py
        ├── assets.py
        ├── generation_common.py
        ├── story
        │   ├── outline.py
        │   ├── episode_outlines.py
        │   ├── episode_contents.py
        │   └── episode_scripts.py
        └── production
            ├── storyboard.py
            └── copywriting.py
```

边界规则：

- `api/projects.py` 只聚合 projects 子路由，不承载具体接口实现。
- `services/projects.py` 是兼容 facade，只重新导出原公开 service 函数。
- `project/common.py` 承载通用序列化、episode 校验和下游 `needs_review` 状态传播。
- `project/generation_common.py` 承载规则文件读取、文本模型调用、JSON 解析和生成上下文公共能力。
- 新增 projects 子能力时优先放入对应业务域模块，不继续堆叠到兼容 facade。

后续预留服务模块：

- `generation`：文本生成、图片生成和 AI 任务记录。
- `assets`：人物示意图、本地素材和资源索引。
- `workspace`：项目工作区目录创建、路径解析和导出文件写入。

本次结构调整不新增数据库表，不新增 Alembic migration。

## 6. 前端模块边界

当前前端保持：

```text
apps/web
├── app
├── components
└── lib
```

约定：

- `app`：Next.js App Router 页面。
- `components/ui`：shadcn/ui 生成的项目级通用 UI 组件。
- `lib/api.ts`：前端 API service 层，页面不直接散落复杂 fetch 逻辑。
- `lib/utils.ts`：通用前端工具函数，当前包含 `cn()` className 合并工具。

项目工作台等复杂页面可在路由目录下使用私有内部目录：

```text
apps/web/app/<route>/_components
apps/web/app/<route>/_hooks
apps/web/app/<route>/_utils
```

使用规则：

- `components/ui`：按钮、输入框、选择器、抽屉、标签、卡片、Tabs、Tooltip 等跨页面基础 UI。
- `_components`：只服务当前路由分组的业务组件。
- `_hooks`：只服务当前路由分组的状态和数据加载逻辑。
- `_utils`：只服务当前路由分组的表单转换、常量和工具函数。

新增通用 UI 时优先使用或扩展 `components/ui`，不要在页面内重复手写基础控件。业务组件仍放在对应路由的 `_components` 下，不把 shadcn 组件当黑盒库使用；组件代码进入项目后可按本项目风格调整。

## 7. 后端接口 Spec

新增或修改后端 API、Pydantic schema、service 业务规则、数据库结构、模型调用规则或安全边界时，在实现前应先创建或更新后端接口 spec。

后端接口 spec 存放位置：

```text
docs/phase-1/backend-specs/<feature-name>.md
```

后端接口 spec 用于描述：

- 接口路径和 HTTP 方法。
- 请求体、响应体和字段校验。
- 业务规则和状态传播。
- 数据库写入边界。
- 错误码和中文错误提示。
- 前端 service 方法对应关系。
- 验收标准。

后端接口 spec 只描述接口合同和实现边界，不替代 PRD 或前端页面 spec。

## 8. 前端页面 Spec

新增页面、重构页面、复杂交互页面、表单规则或 AI 生成工作台页面，在实现前应先创建或更新页面 spec。

页面 spec 存放位置：

```text
docs/phase-1/frontend-specs/<page-name>.md
```

页面 spec 模板：

```text
docs/technical/frontend-page-spec-template.md
```

页面 spec 用于描述：

- 页面目标。
- 用户流程。
- 信息架构。
- 布局结构。
- 字段与控件。
- 交互状态。
- API 依赖。
- 错误提示。
- 桌面端布局要求。
- 验收标准。

页面 spec 只描述前端行为和验收，不替代模块 PRD 或后端接口 spec。

## 9. Spec 拆分规则

前端 spec 和后端 spec 按影响范围拆分，不要求每个功能都机械创建两份。

判断规则：

```text
影响产品范围
 -> 更新模块 PRD

影响 API、数据库、service 规则、模型调用或安全边界
 -> 更新后端接口 Spec

影响页面布局、表单、交互、状态或前端校验
 -> 更新前端页面 Spec

只影响小 bug、文案或样式
 -> 可只改代码，并在必要时同步相关 spec
```

前端 spec 可以保留 API 依赖表，但只用于说明页面调用关系；接口字段、数据库写入、错误码、安全边界和状态传播以后端 spec 为准。

后端 spec 可以保留前端 service 对齐表，但只用于说明接口调用入口；页面布局、按钮动作、交互状态和桌面端布局要求以前端 spec 为准。

## 10. 功能实现流程

新增或调整功能时，统一遵守：

```text
docs/technical/implementation-workflow.md
```

标准推进顺序：

```text
确认需求层级
 -> 更新模块 PRD
 -> 按需更新后端接口 Spec
 -> 按需更新前端页面 Spec
 -> 明确后端、前端、数据库实现边界
 -> 实现代码
 -> 同步文档
 -> 运行验证
```

如果只是小范围 bug fix 或文案样式调整，可以简化流程；但只要影响字段含义、API 行为、数据库结构、AI 生成上下文或页面流程，就必须补齐对应文档。
