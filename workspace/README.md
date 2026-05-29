# 项目工作区

`workspace/` 用于保存短剧项目在本地运行时产生的产物，例如导出文件、人物示意图、生成历史和后续素材引用。

该目录的设计目标是把“项目数据记录”和“项目产物文件”分开：

- 数据库保存结构化数据和流程状态。
- `workspace/projects/<project-id>/` 保存较大的本地文件和可导出的项目产物。

## 目录约定

未来每个短剧项目使用以下结构：

```text
workspace/projects/<project-id>
├── metadata.json
├── exports
├── assets
│   └── characters
├── generations
└── scripts
```

目录说明：

- `metadata.json`：项目级本地 metadata，用于记录文件资源索引、导出信息和生成快照。
- `exports`：Markdown、发布包或其他可导出文件。
- `assets/characters`：人物示意图、人物参考图和后续角色一致性素材。
- `generations`：AI 生成任务的输入快照、提示词、输出结果和错误信息。
- `scripts`：导出的剧本文本、分集剧本或后续制作脚本。

## Git 策略

`workspace/projects/` 下的具体项目产物默认不提交到 GitHub。

当前仓库只提交：

- `workspace/README.md`
- `workspace/projects/.gitkeep`

这样可以保留目录约定，同时避免图片、导出文件、生成结果和本地素材污染仓库。

