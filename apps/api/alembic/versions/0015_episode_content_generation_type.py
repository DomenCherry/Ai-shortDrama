"""add episode content generation type

Revision ID: 0015_episode_content_generation_type
Revises: 0014_storyboard_aggregate
Create Date: 2026-06-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0015_episode_content_generation_type"
down_revision: Union[str, None] = "0014_storyboard_aggregate"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "episode_content_generation_versions",
        sa.Column("generation_type", sa.String(length=24), nullable=False, server_default="create"),
    )
    op.create_index(
        op.f("ix_episode_content_generation_versions_generation_type"),
        "episode_content_generation_versions",
        ["generation_type"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_episode_content_generation_versions_generation_type"),
        table_name="episode_content_generation_versions",
    )
    op.drop_column("episode_content_generation_versions", "generation_type")
