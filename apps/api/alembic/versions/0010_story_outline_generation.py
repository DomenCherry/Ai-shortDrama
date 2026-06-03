"""add story outline generation fields

Revision ID: 0010_story_outline_generation
Revises: 0009_project_asset_snapshot_constraints
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_story_outline_generation"
down_revision: Union[str, None] = "0009_project_asset_snapshot_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("project_story_outlines", sa.Column("story_background", sa.Text(), nullable=True))
    op.add_column("project_story_outlines", sa.Column("story_start", sa.Text(), nullable=True))
    op.add_column("project_story_outlines", sa.Column("plot_structure", sa.Text(), nullable=True))
    op.add_column("project_story_outlines", sa.Column("reversals", sa.Text(), nullable=True))
    op.add_column("project_story_outlines", sa.Column("emotion_curve", sa.Text(), nullable=True))
    op.add_column("project_story_outlines", sa.Column("foreshadowing", sa.Text(), nullable=True))
    op.add_column("project_story_outlines", sa.Column("pacing_advice", sa.Text(), nullable=True))
    op.add_column("project_story_outlines", sa.Column("capacity_advice", sa.Text(), nullable=True))

    op.create_table(
        "project_story_structure_drafts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=24), nullable=False),
        sa.Column("source_filename", sa.String(length=240), nullable=True),
        sa.Column("source_text_excerpt", sa.Text(), nullable=True),
        sa.Column("story_type", sa.Text(), nullable=True),
        sa.Column("goal_model", sa.Text(), nullable=True),
        sa.Column("inciting_event_type", sa.Text(), nullable=True),
        sa.Column("conflict_model", sa.Text(), nullable=True),
        sa.Column("stage_structure", sa.Text(), nullable=True),
        sa.Column("reversal_mechanism", sa.Text(), nullable=True),
        sa.Column("emotion_curve", sa.Text(), nullable=True),
        sa.Column("foreshadowing_pattern", sa.Text(), nullable=True),
        sa.Column("ending_pattern", sa.Text(), nullable=True),
        sa.Column("adaptation_advice", sa.Text(), nullable=True),
        sa.Column("de_specificity_notes", sa.Text(), nullable=True),
        sa.Column("validation_status", sa.String(length=24), nullable=False),
        sa.Column("validation_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_story_structure_drafts_project_id"), "project_story_structure_drafts", ["project_id"])
    op.create_index(op.f("ix_project_story_structure_drafts_status"), "project_story_structure_drafts", ["status"])
    op.create_index(
        op.f("ix_project_story_structure_drafts_validation_status"),
        "project_story_structure_drafts",
        ["validation_status"],
    )
    op.create_index(
        "ix_project_story_structure_drafts_updated_at",
        "project_story_structure_drafts",
        ["updated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_project_story_structure_drafts_updated_at", table_name="project_story_structure_drafts")
    op.drop_index(op.f("ix_project_story_structure_drafts_validation_status"), table_name="project_story_structure_drafts")
    op.drop_index(op.f("ix_project_story_structure_drafts_status"), table_name="project_story_structure_drafts")
    op.drop_index(op.f("ix_project_story_structure_drafts_project_id"), table_name="project_story_structure_drafts")
    op.drop_table("project_story_structure_drafts")

    op.drop_column("project_story_outlines", "capacity_advice")
    op.drop_column("project_story_outlines", "pacing_advice")
    op.drop_column("project_story_outlines", "foreshadowing")
    op.drop_column("project_story_outlines", "emotion_curve")
    op.drop_column("project_story_outlines", "reversals")
    op.drop_column("project_story_outlines", "plot_structure")
    op.drop_column("project_story_outlines", "story_start")
    op.drop_column("project_story_outlines", "story_background")
