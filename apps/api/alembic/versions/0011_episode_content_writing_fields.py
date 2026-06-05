"""add episode content writing fields

Revision ID: 0011_episode_content_fields
Revises: 0010_story_outline_generation
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_episode_content_fields"
down_revision: Union[str, None] = "0010_story_outline_generation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("project_episode_contents", sa.Column("title", sa.String(length=200), nullable=True))
    op.add_column("project_episode_contents", sa.Column("chapter_summary", sa.Text(), nullable=True))
    op.add_column("project_episode_contents", sa.Column("hook", sa.Text(), nullable=True))
    op.add_column(
        "project_episode_contents",
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("project_episode_contents", sa.Column("previous_context_summary", sa.Text(), nullable=True))
    op.add_column("project_episode_contents", sa.Column("quality_check_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("project_episode_contents", "quality_check_notes")
    op.drop_column("project_episode_contents", "previous_context_summary")
    op.drop_column("project_episode_contents", "word_count")
    op.drop_column("project_episode_contents", "hook")
    op.drop_column("project_episode_contents", "chapter_summary")
    op.drop_column("project_episode_contents", "title")
