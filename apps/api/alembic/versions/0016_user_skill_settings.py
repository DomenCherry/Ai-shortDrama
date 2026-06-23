"""add user skill settings

Revision ID: 0016_user_skill_settings
Revises: 0015_episode_content_generation_type
Create Date: 2026-06-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0016_user_skill_settings"
down_revision: Union[str, None] = "0015_episode_content_generation_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_skill_settings",
        sa.Column("skill_name", sa.String(length=120), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_skill_settings")
