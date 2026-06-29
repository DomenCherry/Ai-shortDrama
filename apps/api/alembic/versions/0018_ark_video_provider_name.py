"""normalize Ark video provider name

Revision ID: 0018_ark_video_provider_name
Revises: 0017_video_model_defaults
Create Date: 2026-06-29
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0018_ark_video_provider_name"
down_revision: Union[str, None] = "0017_video_model_defaults"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE model_api_configs "
        "SET provider_name = '火山方舟' "
        "WHERE provider_preset = 'volcengine_seedance_1_5'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE model_api_configs "
        "SET provider_name = '火山方舟 Seedance 1.5 Pro' "
        "WHERE provider_preset = 'volcengine_seedance_1_5'"
    )
