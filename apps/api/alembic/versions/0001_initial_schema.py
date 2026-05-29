"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "model_api_configs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("config_type", sa.String(length=16), nullable=False),
        sa.Column("provider_name", sa.String(length=120), nullable=False),
        sa.Column("api_base_url", sa.Text(), nullable=False),
        sa.Column("api_key_secret", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=160), nullable=False),
        sa.Column("image_size", sa.String(length=40), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_test_status", sa.String(length=24), nullable=False, server_default="untested"),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_model_api_configs_config_type",
        "model_api_configs",
        ["config_type"],
    )

    op.create_table(
        "model_api_test_logs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("config_id", sa.String(length=64), nullable=False),
        sa.Column("config_type", sa.String(length=16), nullable=False),
        sa.Column("request_summary", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("tested_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["config_id"], ["model_api_configs.id"]),
    )
    op.create_index(
        "ix_model_api_test_logs_config_id",
        "model_api_test_logs",
        ["config_id"],
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("idea", sa.Text(), nullable=False),
        sa.Column("target_platform", sa.String(length=80), nullable=True),
        sa.Column("genre", sa.String(length=120), nullable=True),
        sa.Column("episode_count", sa.Integer(), nullable=False),
        sa.Column("episode_duration", sa.Float(), nullable=False),
        sa.Column("total_duration", sa.Float(), nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("style", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("projects")
    op.drop_index("ix_model_api_test_logs_config_id", table_name="model_api_test_logs")
    op.drop_table("model_api_test_logs")
    op.drop_index("ix_model_api_configs_config_type", table_name="model_api_configs")
    op.drop_table("model_api_configs")
