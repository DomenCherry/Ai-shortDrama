"""add project workflow artifacts

Revision ID: 0008_project_workflow_artifacts
Revises: 0007_world_books
Create Date: 2026-06-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_project_workflow_artifacts"
down_revision: Union[str, None] = "0007_world_books"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_story_outlines",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("logline", sa.Text(), nullable=True),
        sa.Column("core_conflict", sa.Text(), nullable=True),
        sa.Column("main_goal", sa.Text(), nullable=True),
        sa.Column("character_arcs", sa.Text(), nullable=True),
        sa.Column("ending_direction", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index(op.f("ix_project_story_outlines_project_id"), "project_story_outlines", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_story_outlines_status"), "project_story_outlines", ["status"], unique=False)

    op.create_table(
        "project_episode_outlines",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("hook", sa.Text(), nullable=True),
        sa.Column("conflict", sa.Text(), nullable=True),
        sa.Column("reversal", sa.Text(), nullable=True),
        sa.Column("cliffhanger", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "episode_no", name="uq_project_episode_outlines_project_episode"),
    )
    op.create_index(op.f("ix_project_episode_outlines_episode_no"), "project_episode_outlines", ["episode_no"], unique=False)
    op.create_index(op.f("ix_project_episode_outlines_project_id"), "project_episode_outlines", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_episode_outlines_status"), "project_episode_outlines", ["status"], unique=False)

    op.create_table(
        "project_episode_contents",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("detailed_content", sa.Text(), nullable=True),
        sa.Column("key_beats", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "episode_no", name="uq_project_episode_contents_project_episode"),
    )
    op.create_index(op.f("ix_project_episode_contents_episode_no"), "project_episode_contents", ["episode_no"], unique=False)
    op.create_index(op.f("ix_project_episode_contents_project_id"), "project_episode_contents", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_episode_contents_status"), "project_episode_contents", ["status"], unique=False)

    op.create_table(
        "project_episode_scripts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("scene_text", sa.Text(), nullable=True),
        sa.Column("dialogue", sa.Text(), nullable=True),
        sa.Column("action_notes", sa.Text(), nullable=True),
        sa.Column("voiceover", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "episode_no", name="uq_project_episode_scripts_project_episode"),
    )
    op.create_index(op.f("ix_project_episode_scripts_episode_no"), "project_episode_scripts", ["episode_no"], unique=False)
    op.create_index(op.f("ix_project_episode_scripts_project_id"), "project_episode_scripts", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_episode_scripts_status"), "project_episode_scripts", ["status"], unique=False)

    op.create_table(
        "project_storyboard_shots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("shot_no", sa.Integer(), nullable=False),
        sa.Column("scene", sa.Text(), nullable=True),
        sa.Column("visual_prompt", sa.Text(), nullable=True),
        sa.Column("camera", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("dialogue_or_voiceover", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_storyboard_shots_episode_no"), "project_storyboard_shots", ["episode_no"], unique=False)
    op.create_index(op.f("ix_project_storyboard_shots_project_id"), "project_storyboard_shots", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_storyboard_shots_status"), "project_storyboard_shots", ["status"], unique=False)

    op.create_table(
        "project_copywriting",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("subtitles", sa.Text(), nullable=True),
        sa.Column("platform_title", sa.String(length=200), nullable=True),
        sa.Column("platform_description", sa.Text(), nullable=True),
        sa.Column("publish_copy", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "episode_no", name="uq_project_copywriting_project_episode"),
    )
    op.create_index(op.f("ix_project_copywriting_episode_no"), "project_copywriting", ["episode_no"], unique=False)
    op.create_index(op.f("ix_project_copywriting_project_id"), "project_copywriting", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_copywriting_status"), "project_copywriting", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_project_copywriting_status"), table_name="project_copywriting")
    op.drop_index(op.f("ix_project_copywriting_project_id"), table_name="project_copywriting")
    op.drop_index(op.f("ix_project_copywriting_episode_no"), table_name="project_copywriting")
    op.drop_table("project_copywriting")

    op.drop_index(op.f("ix_project_storyboard_shots_status"), table_name="project_storyboard_shots")
    op.drop_index(op.f("ix_project_storyboard_shots_project_id"), table_name="project_storyboard_shots")
    op.drop_index(op.f("ix_project_storyboard_shots_episode_no"), table_name="project_storyboard_shots")
    op.drop_table("project_storyboard_shots")

    op.drop_index(op.f("ix_project_episode_scripts_status"), table_name="project_episode_scripts")
    op.drop_index(op.f("ix_project_episode_scripts_project_id"), table_name="project_episode_scripts")
    op.drop_index(op.f("ix_project_episode_scripts_episode_no"), table_name="project_episode_scripts")
    op.drop_table("project_episode_scripts")

    op.drop_index(op.f("ix_project_episode_contents_status"), table_name="project_episode_contents")
    op.drop_index(op.f("ix_project_episode_contents_project_id"), table_name="project_episode_contents")
    op.drop_index(op.f("ix_project_episode_contents_episode_no"), table_name="project_episode_contents")
    op.drop_table("project_episode_contents")

    op.drop_index(op.f("ix_project_episode_outlines_status"), table_name="project_episode_outlines")
    op.drop_index(op.f("ix_project_episode_outlines_project_id"), table_name="project_episode_outlines")
    op.drop_index(op.f("ix_project_episode_outlines_episode_no"), table_name="project_episode_outlines")
    op.drop_table("project_episode_outlines")

    op.drop_index(op.f("ix_project_story_outlines_status"), table_name="project_story_outlines")
    op.drop_index(op.f("ix_project_story_outlines_project_id"), table_name="project_story_outlines")
    op.drop_table("project_story_outlines")
