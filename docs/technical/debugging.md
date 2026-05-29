# 本地调试说明

## 1. 调试前准备

当前项目分为：

- 前端：Next.js，位于 `apps/web`
- 后端：FastAPI，位于 `apps/api`
- 数据库：PostgreSQL，通过 Docker Compose 启动

后端 Python 环境统一使用 Python 3.11。

首次调试前建议执行：

```bash
npm run setup:api
npm install --prefix apps/web
```

## 2. 启动数据库

先确保 Docker 已启动，然后执行：

```bash
docker compose up -d postgres
npm run db:migrate
```

如果数据库已经启动并且迁移过，后续一般只需要确认容器运行即可。

## 3. 调试后端 FastAPI

启动后端：

```bash
npm run dev:api
```

后端地址：

```text
http://127.0.0.1:8000
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

可以在 API 文档里直接测试接口，例如：

- `GET /health`
- `POST /api/projects`
- `POST /api/model-configs`

## 4. IDE 断点调试后端

如果使用 VS Code 或 Cursor，可以在项目根目录创建 `.vscode/launch.json`，配置如下：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--app-dir",
        "apps/api",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

然后可以在后端文件里打断点，例如：

```text
apps/api/app/services/projects.py
apps/api/app/services/model_configs.py
apps/api/app/api/projects.py
apps/api/app/api/model_configs.py
```

## 5. 调试前端 Next.js

启动前端：

```bash
npm run dev:web
```

前端地址：

```text
http://127.0.0.1:3000
```

主要页面：

- 首页：`/`
- 创建项目：`/projects/new`
- 模型配置：`/settings`

前端调试建议使用浏览器 DevTools：

- Console：查看页面报错
- Network：查看 API 请求与响应
- Elements：检查页面结构和样式

## 6. 推荐日常调试顺序

```bash
docker compose up -d postgres
npm run db:migrate
npm run dev:api
npm run dev:web
```

然后打开：

```text
http://127.0.0.1:3000
```

后端问题优先用 IDE 断点和 API 文档定位；前端问题优先用浏览器 DevTools 定位。

