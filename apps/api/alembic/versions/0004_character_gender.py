"""add character gender fields

Revision ID: 0004_character_gender
Revises: 0003_character_visual_assets
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_character_gender"
down_revision: Union[str, None] = "0003_character_visual_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("character_cards", sa.Column("gender", sa.String(length=4), nullable=True))
    op.add_column("project_character_snapshots", sa.Column("gender", sa.String(length=4), nullable=True))

    # 旧角色卡没有性别来源，只能先回填为“女”，之后用户可在角色详情中手动修正。
    op.execute("UPDATE character_cards SET gender = '女' WHERE gender IS NULL")
    # 项目快照优先继承来源角色卡的回填结果，避免同一角色在库和项目快照中不一致。
    op.execute(
        """
        UPDATE project_character_snapshots
        SET gender = character_cards.gender
        FROM character_cards
        WHERE project_character_snapshots.source_character_card_id = character_cards.id
        """
    )
    op.execute("UPDATE project_character_snapshots SET gender = '女' WHERE gender IS NULL")

    op.alter_column("character_cards", "gender", existing_type=sa.String(length=4), nullable=False)
    op.alter_column("project_character_snapshots", "gender", existing_type=sa.String(length=4), nullable=False)
    op.create_index("ix_character_cards_gender", "character_cards", ["gender"])
    op.create_check_constraint("ck_character_cards_gender", "character_cards", "gender in ('男', '女')")
    op.create_check_constraint(
        "ck_project_character_snapshots_gender",
        "project_character_snapshots",
        "gender in ('男', '女')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_project_character_snapshots_gender", "project_character_snapshots", type_="check")
    op.drop_constraint("ck_character_cards_gender", "character_cards", type_="check")
    op.drop_index("ix_character_cards_gender", table_name="character_cards")
    op.drop_column("project_character_snapshots", "gender")
    op.drop_column("character_cards", "gender")
