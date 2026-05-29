"""add provider metadata to model api configs

Revision ID: 0005_model_provider_config
Revises: 0004_character_gender
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_model_provider_config"
down_revision: Union[str, None] = "0004_character_gender"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "model_api_configs",
        sa.Column("provider_mode", sa.String(length=16), nullable=False, server_default="custom"),
    )
    op.add_column("model_api_configs", sa.Column("provider_preset", sa.String(length=80), nullable=True))
    op.add_column("model_api_configs", sa.Column("endpoint_path", sa.String(length=160), nullable=True))
    op.add_column(
        "model_api_configs",
        sa.Column("supports_reference_image", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # 旧图片配置保持原有 OpenAI-compatible 路径，避免迁移后测试和生成接口找不到 endpoint。
    op.execute(
        """
        update model_api_configs
        set endpoint_path = '/images/generations'
        where config_type = 'image' and endpoint_path is null
        """
    )

    op.create_check_constraint(
        "ck_model_api_configs_provider_mode",
        "model_api_configs",
        "provider_mode in ('preset', 'custom')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_model_api_configs_provider_mode", "model_api_configs", type_="check")
    op.drop_column("model_api_configs", "supports_reference_image")
    op.drop_column("model_api_configs", "endpoint_path")
    op.drop_column("model_api_configs", "provider_preset")
    op.drop_column("model_api_configs", "provider_mode")
