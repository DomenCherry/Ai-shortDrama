"""project asset snapshot constraints

Revision ID: 0009_asset_snapshot_constraints
Revises: 0008_project_workflow_artifacts
Create Date: 2026-06-03
"""

from alembic import op


revision = "0009_asset_snapshot_constraints"
down_revision = "0008_project_workflow_artifacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_project_world_snapshots_project",
        "project_world_snapshots",
        ["project_id"],
    )
    op.create_unique_constraint(
        "uq_project_character_snapshots_project_source",
        "project_character_snapshots",
        ["project_id", "source_character_card_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_project_character_snapshots_project_source",
        "project_character_snapshots",
        type_="unique",
    )
    op.drop_constraint(
        "uq_project_world_snapshots_project",
        "project_world_snapshots",
        type_="unique",
    )
