# AI 短剧创作工作台

这是一个面向个人创作者的 AI 短剧制作工具，目标是帮助用户从创意出发，逐步完成选题、故事大纲、人物设定、人物示意图、分集大纲和单集剧本。

## 项目结构

```text
apps
├── api   # FastAPI 后端服务
└── web   # Next.js 前端工作台
docs      # 产品、阶段 PRD 和详细设计文档
```

## 本地开发

1. 复制环境变量：

```bash
cp .env.example .env
```

2. 启动后端：

```bash
docker compose up -d postgres
npm run setup:api
npm run db:migrate
npm run dev:api
```

3. 启动前端：

```bash
npm install --prefix apps/web
npm run dev:web
```

默认地址：

- 前端：http://localhost:3000
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 数据库

项目使用 PostgreSQL 作为主数据库，本地开发通过 `docker-compose.yml` 启动。

## Python 环境

后端统一使用 Python 3.11。推荐本地命令：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
```

默认连接地址：

```text
postgresql+psycopg://ai_short_drama:ai_short_drama@127.0.0.1:5432/ai_short_drama
```

## 当前框架能力

- 模型 API 配置接口
- 模型 API 连通性测试接口
- 项目创建接口
- 项目时长强校验
- 前端设置页
- 前端项目创建页
