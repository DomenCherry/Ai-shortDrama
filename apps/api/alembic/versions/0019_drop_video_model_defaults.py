"""drop video model defaults

Revision ID: 0019_drop_video_model_defaults
Revises: 0018_ark_video_provider_name
Create Date: 2026-06-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0019_drop_video_model_defaults"
down_revision: Union[str, None] = "0018_ark_video_provider_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if _has_column("model_api_configs", "video_defaults"):
        op.drop_column("model_api_configs", "video_defaults")


def downgrade() -> None:
    if not _has_column("model_api_configs", "video_defaults"):
        op.add_column("model_api_configs", sa.Column("video_defaults", sa.Text(), nullable=True))
