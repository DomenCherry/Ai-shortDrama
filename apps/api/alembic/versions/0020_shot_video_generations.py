"""add shot video generation records

Revision ID: 0020_shot_video_generations
Revises: 0019_drop_video_model_defaults
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0020_shot_video_generations"
down_revision: Union[str, None] = "0019_drop_video_model_defaults"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_shot_video_generations",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.String(length=64), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("storyboard_id", sa.String(length=64), sa.ForeignKey("project_storyboards.id"), nullable=False),
        sa.Column("shot_id", sa.String(length=64), sa.ForeignKey("project_storyboard_shots.id"), nullable=False),
        sa.Column("prompt_id", sa.String(length=64), sa.ForeignKey("project_shot_prompts.id"), nullable=True),
        sa.Column("source_shot_revision", sa.Integer(), nullable=False),
        sa.Column("source_prompt_revision", sa.Integer(), nullable=True),
        sa.Column("video_prompt_snapshot", sa.Text(), nullable=False),
        sa.Column("negative_prompt_snapshot", sa.Text(), nullable=True),
        sa.Column("reference_asset_ids", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("model_config_id", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=160), nullable=False),
        sa.Column("provider_preset", sa.String(length=80), nullable=True),
        sa.Column("provider_task_id", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="queued"),
        sa.Column("result_url", sa.Text(), nullable=True),
        sa.Column("local_asset_path", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_payload_snapshot", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("adopted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("adopted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_project_shot_video_generations_project_id"), "project_shot_video_generations", ["project_id"])
    op.create_index(op.f("ix_project_shot_video_generations_episode_no"), "project_shot_video_generations", ["episode_no"])
    op.create_index(op.f("ix_project_shot_video_generations_storyboard_id"), "project_shot_video_generations", ["storyboard_id"])
    op.create_index(op.f("ix_project_shot_video_generations_shot_id"), "project_shot_video_generations", ["shot_id"])
    op.create_index(op.f("ix_project_shot_video_generations_prompt_id"), "project_shot_video_generations", ["prompt_id"])
    op.create_index(op.f("ix_project_shot_video_generations_model_config_id"), "project_shot_video_generations", ["model_config_id"])
    op.create_index(op.f("ix_project_shot_video_generations_provider_task_id"), "project_shot_video_generations", ["provider_task_id"])
    op.create_index(op.f("ix_project_shot_video_generations_status"), "project_shot_video_generations", ["status"])
    op.create_index(op.f("ix_project_shot_video_generations_adopted"), "project_shot_video_generations", ["adopted"])


def downgrade() -> None:
    op.drop_index(op.f("ix_project_shot_video_generations_adopted"), table_name="project_shot_video_generations")
    op.drop_index(op.f("ix_project_shot_video_generations_status"), table_name="project_shot_video_generations")
    op.drop_index(op.f("ix_project_shot_video_generations_provider_task_id"), table_name="project_shot_video_generations")
    op.drop_index(op.f("ix_project_shot_video_generations_model_config_id"), table_name="project_shot_video_generations")
    op.drop_index(op.f("ix_project_shot_video_generations_prompt_id"), table_name="project_shot_video_generations")
    op.drop_index(op.f("ix_project_shot_video_generations_shot_id"), table_name="project_shot_video_generations")
    op.drop_index(op.f("ix_project_shot_video_generations_storyboard_id"), table_name="project_shot_video_generations")
    op.drop_index(op.f("ix_project_shot_video_generations_episode_no"), table_name="project_shot_video_generations")
    op.drop_index(op.f("ix_project_shot_video_generations_project_id"), table_name="project_shot_video_generations")
    op.drop_table("project_shot_video_generations")
