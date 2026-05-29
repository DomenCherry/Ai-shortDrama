"""add character card library

Revision ID: 0002_character_cards
Revises: 0001_initial_schema
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_character_cards"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "character_cards",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("role_type", sa.String(length=40), nullable=False),
        sa.Column("identity", sa.String(length=200), nullable=False),
        sa.Column("background", sa.Text(), nullable=True),
        sa.Column("personality", sa.Text(), nullable=True),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("motivation", sa.Text(), nullable=True),
        sa.Column("secret", sa.Text(), nullable=True),
        sa.Column("conflict_points", sa.Text(), nullable=True),
        sa.Column("relationship_notes", sa.Text(), nullable=True),
        sa.Column("speech_style", sa.Text(), nullable=True),
        sa.Column("catchphrases", sa.Text(), nullable=True),
        sa.Column("emotional_arc", sa.Text(), nullable=True),
        sa.Column("story_function", sa.Text(), nullable=True),
        sa.Column("visual_description", sa.Text(), nullable=True),
        sa.Column("image_keywords", sa.Text(), nullable=True),
        sa.Column("reference_image_url", sa.Text(), nullable=True),
        sa.Column("reference_local_path", sa.Text(), nullable=True),
        # 版本字段支撑项目快照的来源追踪，后续可提示用户来源角色卡已有新版本。
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # archived 代替硬删除，避免破坏历史项目来源。
        sa.Column("status", sa.String(length=24), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_character_cards_name", "character_cards", ["name"])
    op.create_index("ix_character_cards_role_type", "character_cards", ["role_type"])
    op.create_index("ix_character_cards_status", "character_cards", ["status"])

    op.create_table(
        "project_character_snapshots",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("source_character_card_id", sa.String(length=64), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("role_type", sa.String(length=40), nullable=False),
        # 快照内容固定为加载时的角色卡内容，项目编辑不能回写原始角色卡。
        sa.Column("snapshot_content", sa.Text(), nullable=False),
        sa.Column("visual_description", sa.Text(), nullable=True),
        sa.Column("reference_image_url", sa.Text(), nullable=True),
        sa.Column("reference_local_path", sa.Text(), nullable=True),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["source_character_card_id"], ["character_cards.id"]),
    )
    op.create_index("ix_project_character_snapshots_project_id", "project_character_snapshots", ["project_id"])
    op.create_index(
        "ix_project_character_snapshots_source_character_card_id",
        "project_character_snapshots",
        ["source_character_card_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_project_character_snapshots_source_character_card_id",
        table_name="project_character_snapshots",
    )
    op.drop_index("ix_project_character_snapshots_project_id", table_name="project_character_snapshots")
    op.drop_table("project_character_snapshots")
    op.drop_index("ix_character_cards_status", table_name="character_cards")
    op.drop_index("ix_character_cards_role_type", table_name="character_cards")
    op.drop_index("ix_character_cards_name", table_name="character_cards")
    op.drop_table("character_cards")
