# 前端 UI 组件库规范

## 1. 目标

本文档用于维护本项目当前可用的前端 UI 组件库，并固化后续前端实现前的组件复用检查流程。

目标是避免在页面中重复手写按钮、输入框、选择器、抽屉、标签等基础控件，让前端界面在视觉、交互和代码结构上保持一致。

## 2. 当前技术栈

当前前端 UI 基础设施为：

- Next.js App Router。
- TypeScript。
- Tailwind CSS。
- shadcn/ui。
- lucide-react 图标。

shadcn/ui 组件源码进入本项目后，由本项目直接维护。它不是不可修改的黑盒依赖，但修改时必须保持通用性，不能把具体业务逻辑写入 `components/ui`。

## 3. 目录约定

```text
apps/web
├── app
├── components
│   └── ui
└── lib
    └── utils.ts
```

目录职责：

- `apps/web/components/ui`：跨页面可复用的基础 UI 组件。
- `apps/web/lib/utils.ts`：通用工具函数，当前包含 `cn()` className 合并工具。
- `apps/web/app/<route>/_components`：只服务当前路由的业务组件。
- `apps/web/app/<route>/_hooks`：只服务当前路由的数据加载和状态逻辑。
- `apps/web/app/<route>/_utils`：只服务当前路由的表单转换、常量和工具函数。

## 4. 当前组件清单

| 组件 | 文件 | 推荐用途 |
| --- | --- | --- |
| Button | `apps/web/components/ui/button.tsx` | 主按钮、次按钮、图标按钮、危险操作按钮 |
| Input | `apps/web/components/ui/input.tsx` | 单行文本、数字、密码等输入 |
| Textarea | `apps/web/components/ui/textarea.tsx` | 长文本、提示词、故事内容输入 |
| Select | `apps/web/components/ui/select.tsx` | 状态、类型、枚举值选择 |
| Badge | `apps/web/components/ui/badge.tsx` | 状态标签、类型标签、轻量标记 |
| Card | `apps/web/components/ui/card.tsx` | 独立信息块、列表卡片、少量重复项 |
| Sheet | `apps/web/components/ui/sheet.tsx` | 抽屉、侧边选择器、轻量配置面板 |
| Tabs | `apps/web/components/ui/tabs.tsx` | 同级内容切换 |
| Tooltip | `apps/web/components/ui/tooltip.tsx` | 图标按钮、紧凑操作的悬浮说明 |

导入示例：

```tsx
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
```

## 5. 前端实现前检查顺序

每次新增或修改前端页面、表单、工作台模块或共享组件前，必须按以下顺序检查：

1. 查 `docs/technical/ui-component-library.md`，确认是否已有基础 UI 组件。
2. 查 `apps/web/components/ui`，确认是否已有可直接复用或轻量扩展的组件。
3. 查当前路由的 `_components`，确认是否已有业务组件可复用。
4. 只有在现有组件无法满足时，才新增基础 UI 组件或业务组件。

基础控件不得在页面文件中重复手写。例如按钮、输入框、文本域、选择器、抽屉、状态标签、卡片、Tabs、Tooltip 应优先使用 `components/ui`。

## 6. 新增组件规则

新增通用 UI 组件时遵守：

- 优先通过 shadcn/ui CLI 添加组件。
- 组件源码放入 `apps/web/components/ui`。
- 新增后必须同步更新本文档的“当前组件清单”。
- 组件应保持通用，不接收具体业务对象作为 props。
- 业务文案、业务校验、API 调用和数据转换不得进入 `components/ui`。

如果只是某个页面的业务组合，例如项目资产抽屉、角色卡表单、故事大纲编辑器，应放在对应路由的 `_components`，不要放入 `components/ui`。

## 7. 维护规则

- 不引入第二套 UI 框架，除非已有 shadcn/ui 方案无法支撑且经过单独技术评估。
- 修改 `components/ui` 时，需要检查所有引用该组件的页面是否仍可用。
- 删除或重命名 UI 组件时，必须同步更新本文档和引用方。
- 页面局部样式优先通过 `className` 和 `cn()` 组合实现，不复制一份新的基础控件。
- 当某个业务组件在三个以上页面重复出现时，再评估是否抽成跨路由业务组件；不要默认放入 `components/ui`。

## 8. 验证

修改 UI 组件或前端页面后至少运行：

```bash
npm --prefix apps/web run typecheck
```

如果新增、删除或重命名 `components/ui` 组件，还应检查组件清单：

```bash
find apps/web/components/ui -maxdepth 1 -type f -print | sort
rg -n "components/ui|shadcn|UI 组件库" docs
```
