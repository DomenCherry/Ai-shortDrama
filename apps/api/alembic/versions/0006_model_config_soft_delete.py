"""add soft delete to model api configs

Revision ID: 0006_model_config_soft_delete
Revises: 0005_model_provider_config
Create Date: 2026-06-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_model_config_soft_delete"
down_revision: Union[str, None] = "0005_model_provider_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "model_api_configs",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("model_api_configs", "deleted_at")
