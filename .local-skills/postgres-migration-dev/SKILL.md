---
name: postgres-migration-dev
description: 修改 PostgreSQL、SQLAlchemy 模型或 Alembic migration 时使用。适用于新增表、改字段、加索引、调整约束、排查数据库迁移和查询性能问题。
---

# PostgreSQL 与迁移开发

## 使用场景

涉及以下内容时使用：

- 修改 `apps/api/app/models/db_models.py`。
- 新增或修改 Alembic migration。
- 调整 PostgreSQL 字段类型、索引、外键、约束。
- 设计后续素材、生成任务、发布数据、账号权限等表。

## 项目约定

- PostgreSQL 是主数据库。
- SQLAlchemy 是 ORM。
- Alembic 管理 schema 版本。
- 本地数据库通过 `docker-compose.yml` 启动。
- 不使用 SQLite 作为主数据库或测试替代。

## 建模原则

- 主键使用字符串 ID，保持和当前模型一致。
- 时间字段使用 timezone-aware `DateTime(timezone=True)`。
- 长文本使用 `Text`。
- 状态字段先用短字符串，后续稳定后再考虑枚举约束。
- 外键关系需要明确删除策略；不确定时不要级联删除业务数据。
- 查询频繁的过滤字段应考虑索引。

## 迁移流程

1. 修改 SQLAlchemy 模型。
2. 新增 Alembic migration。
3. 检查离线 SQL。
4. Docker 可用时执行在线迁移。
5. 验证 API 读写行为。

## 验证

离线 SQL：

```bash
npm run db:migrate -- --sql
```

在线迁移：

```bash
docker compose up -d postgres
npm run db:migrate
```

## 约束

- 不要在应用启动时偷偷改表结构。
- 不要跳过 migration 直接依赖 `metadata.create_all`。
- 不要把图片、视频、音频二进制文件直接存入数据库。
- 媒体文件只在数据库保存 URL、路径、状态、元数据和关联关系。

