"""add video model defaults

Revision ID: 0017_video_model_defaults
Revises: 0016_user_skill_settings
Create Date: 2026-06-29
"""
from typing import Sequence, Union


revision: str = "0017_video_model_defaults"
down_revision: Union[str, None] = "0016_user_skill_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
