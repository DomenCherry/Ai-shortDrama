"""add episode content generation versions

Revision ID: 0012_episode_content_generations
Revises: 0011_episode_content_fields
Create Date: 2026-06-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012_episode_content_generations"
down_revision: Union[str, None] = "0011_episode_content_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "episode_content_generation_versions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=True),
        sa.Column("input_snapshot", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("client_request_id", sa.String(length=80), nullable=False),
        sa.Column("model_config_id", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=160), nullable=True),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("adopted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "episode_no",
            "client_request_id",
            name="uq_episode_content_generations_request",
        ),
    )
    op.create_index(
        op.f("ix_episode_content_generation_versions_project_id"),
        "episode_content_generation_versions",
        ["project_id"],
    )
    op.create_index(
        op.f("ix_episode_content_generation_versions_episode_no"),
        "episode_content_generation_versions",
        ["episode_no"],
    )
    op.create_index(
        op.f("ix_episode_content_generation_versions_status"),
        "episode_content_generation_versions",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_episode_content_generation_versions_status"), table_name="episode_content_generation_versions")
    op.drop_index(op.f("ix_episode_content_generation_versions_episode_no"), table_name="episode_content_generation_versions")
    op.drop_index(op.f("ix_episode_content_generation_versions_project_id"), table_name="episode_content_generation_versions")
    op.drop_table("episode_content_generation_versions")
