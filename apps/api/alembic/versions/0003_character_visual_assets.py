"""add character visual asset fields

Revision ID: 0003_character_visual_assets
Revises: 0002_character_cards
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_character_visual_assets"
down_revision: Union[str, None] = "0002_character_cards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("character_cards", sa.Column("turnaround_prompt", sa.Text(), nullable=True))
    op.add_column("character_cards", sa.Column("turnaround_image_url", sa.Text(), nullable=True))
    op.add_column("character_cards", sa.Column("turnaround_local_path", sa.Text(), nullable=True))
    op.add_column("character_cards", sa.Column("turnaround_generation_prompt", sa.Text(), nullable=True))
    # none/generated/confirmed/failed 表示三视图候选图是否已被用户确认。
    op.add_column(
        "character_cards",
        sa.Column("turnaround_status", sa.String(length=24), nullable=False, server_default="none"),
    )
    op.add_column(
        "character_cards",
        sa.Column("turnaround_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("character_cards", sa.Column("turnaround_confirmed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("character_cards", "turnaround_confirmed_at")
    op.drop_column("character_cards", "turnaround_version")
    op.drop_column("character_cards", "turnaround_status")
    op.drop_column("character_cards", "turnaround_generation_prompt")
    op.drop_column("character_cards", "turnaround_local_path")
    op.drop_column("character_cards", "turnaround_image_url")
    op.drop_column("character_cards", "turnaround_prompt")
