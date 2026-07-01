"""add world books

Revision ID: 0007_world_books
Revises: 0006_model_config_soft_delete
Create Date: 2026-06-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_world_books"
down_revision: Union[str, None] = "0006_model_config_soft_delete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "world_books",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("genre", sa.String(length=120), nullable=False),
        sa.Column("era_background", sa.Text(), nullable=True),
        sa.Column("world_rules", sa.Text(), nullable=False),
        sa.Column("organizations", sa.Text(), nullable=True),
        sa.Column("locations", sa.Text(), nullable=True),
        sa.Column("social_structure", sa.Text(), nullable=True),
        sa.Column("taboo_or_constraints", sa.Text(), nullable=True),
        sa.Column("tone_style", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        # 版本字段用于项目快照判断来源世界观是否已更新。
        sa.Column("version", sa.Integer(), nullable=False),
        # archived 代替硬删除，避免破坏历史项目世界观快照的来源追踪。
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_world_books_genre"), "world_books", ["genre"], unique=False)
    op.create_index(op.f("ix_world_books_name"), "world_books", ["name"], unique=False)
    op.create_index(op.f("ix_world_books_status"), "world_books", ["status"], unique=False)

    op.create_table(
        "world_entries",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("world_book_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("entry_type", sa.String(length=40), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("applicable_scope", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        # disabled 条目不进入项目快照，但保留在资产库中便于恢复。
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["world_book_id"], ["world_books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_world_entries_entry_type"), "world_entries", ["entry_type"], unique=False)
    op.create_index(op.f("ix_world_entries_status"), "world_entries", ["status"], unique=False)
    op.create_index(op.f("ix_world_entries_title"), "world_entries", ["title"], unique=False)
    op.create_index(op.f("ix_world_entries_world_book_id"), "world_entries", ["world_book_id"], unique=False)

    op.create_table(
        "project_world_snapshots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("source_world_book_id", sa.String(length=64), nullable=False),
        # 快照记录加载时的来源版本，后续可提示项目上下文是否落后。
        sa.Column("source_version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("genre", sa.String(length=120), nullable=False),
        # 快照内容固定为加载时的资产内容，项目编辑不能回写世界观库。
        sa.Column("snapshot_content", sa.Text(), nullable=False),
        # 只固化加载时 active 条目，避免 disabled 条目进入生成上下文。
        sa.Column("entry_snapshot_content", sa.Text(), nullable=False),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["source_world_book_id"], ["world_books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_world_snapshots_project_id"), "project_world_snapshots", ["project_id"], unique=False)
    op.create_index(
        op.f("ix_project_world_snapshots_source_world_book_id"),
        "project_world_snapshots",
        ["source_world_book_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_project_world_snapshots_source_world_book_id"), table_name="project_world_snapshots")
    op.drop_index(op.f("ix_project_world_snapshots_project_id"), table_name="project_world_snapshots")
    op.drop_table("project_world_snapshots")

    op.drop_index(op.f("ix_world_entries_world_book_id"), table_name="world_entries")
    op.drop_index(op.f("ix_world_entries_title"), table_name="world_entries")
    op.drop_index(op.f("ix_world_entries_status"), table_name="world_entries")
    op.drop_index(op.f("ix_world_entries_entry_type"), table_name="world_entries")
    op.drop_table("world_entries")

    op.drop_index(op.f("ix_world_books_status"), table_name="world_books")
    op.drop_index(op.f("ix_world_books_name"), table_name="world_books")
    op.drop_index(op.f("ix_world_books_genre"), table_name="world_books")
    op.drop_table("world_books")
