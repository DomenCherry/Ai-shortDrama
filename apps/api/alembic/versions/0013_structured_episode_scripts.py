"""add structured episode scripts

Revision ID: 0013_structured_scripts
Revises: 0012_episode_content_generations
Create Date: 2026-06-18
"""
import json
from typing import Sequence, Union
from uuid import uuid4

from alembic import context, op
import sqlalchemy as sa


revision: str = "0013_structured_scripts"
down_revision: Union[str, None] = "0012_episode_content_generations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("project_episode_scripts", sa.Column("title", sa.String(length=120), nullable=True))
    op.add_column("project_episode_scripts", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("project_episode_scripts", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("project_episode_scripts", sa.Column("source_content_version", sa.String(length=160), nullable=True))
    op.add_column("project_episode_scripts", sa.Column("auto_duration_seconds", sa.Float(), nullable=False, server_default="0"))
    op.add_column("project_episode_scripts", sa.Column("manual_duration_seconds", sa.Float(), nullable=True))
    op.add_column("project_episode_scripts", sa.Column("effective_duration_seconds", sa.Float(), nullable=False, server_default="0"))
    op.add_column("project_episode_scripts", sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "project_script_scenes",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("script_id", sa.String(length=64), sa.ForeignKey("project_episode_scripts.id"), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("time_of_day", sa.String(length=24), nullable=True),
        sa.Column("interior_exterior", sa.String(length=24), nullable=True),
        sa.Column("character_snapshot_ids", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("auto_duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("manual_duration_seconds", sa.Float(), nullable=True),
        sa.Column("effective_duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("story_purpose", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("script_id", "sort_order", name="uq_project_script_scenes_order"),
    )
    op.create_index(op.f("ix_project_script_scenes_script_id"), "project_script_scenes", ["script_id"])

    op.create_table(
        "project_script_blocks",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("scene_id", sa.String(length=64), sa.ForeignKey("project_script_scenes.id"), nullable=False),
        sa.Column("block_type", sa.String(length=24), nullable=False),
        sa.Column("character_snapshot_id", sa.String(length=64), sa.ForeignKey("project_character_snapshots.id"), nullable=True),
        sa.Column("temporary_speaker_name", sa.String(length=120), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("emotion", sa.String(length=120), nullable=True),
        sa.Column("performance_note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("scene_id", "sort_order", name="uq_project_script_blocks_order"),
    )
    op.create_index(op.f("ix_project_script_blocks_scene_id"), "project_script_blocks", ["scene_id"])
    op.create_index(op.f("ix_project_script_blocks_character_snapshot_id"), "project_script_blocks", ["character_snapshot_id"])

    op.create_table(
        "project_episode_script_versions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("script_id", sa.String(length=64), sa.ForeignKey("project_episode_scripts.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source_content_version", sa.String(length=160), nullable=True),
        sa.Column("snapshot", sa.Text(), nullable=False),
        sa.Column("change_source", sa.String(length=32), nullable=False),
        sa.Column("generation_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("script_id", "version", name="uq_project_episode_script_versions_number"),
    )
    op.create_index(op.f("ix_project_episode_script_versions_script_id"), "project_episode_script_versions", ["script_id"])

    op.create_table(
        "project_script_generations",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.String(length=64), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("generation_scope", sa.String(length=24), nullable=False),
        sa.Column("target_scene_id", sa.String(length=64), nullable=True),
        sa.Column("target_block_ids", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("rewrite_preset", sa.String(length=40), nullable=True),
        sa.Column("instruction", sa.Text(), nullable=True),
        sa.Column("base_script_version", sa.Integer(), nullable=True),
        sa.Column("base_script_revision", sa.Integer(), nullable=True),
        sa.Column("input_snapshot", sa.Text(), nullable=False),
        sa.Column("output_snapshot", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="candidate"),
        sa.Column("client_request_id", sa.String(length=80), nullable=False),
        sa.Column("model_config_id", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=160), nullable=True),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("adopted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "episode_no", "generation_scope", "client_request_id", name="uq_project_script_generations_request"),
    )
    for column in ("project_id", "episode_no", "generation_scope", "status"):
        op.create_index(op.f(f"ix_project_script_generations_{column}"), "project_script_generations", [column])

    op.create_table(
        "project_script_check_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("script_id", sa.String(length=64), sa.ForeignKey("project_episode_scripts.id"), nullable=False),
        sa.Column("script_version", sa.Integer(), nullable=False),
        sa.Column("script_revision", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=24), nullable=False),
        sa.Column("semantic_check_status", sa.String(length=24), nullable=False),
        sa.Column("issues", sa.Text(), nullable=False),
        sa.Column("model_config_id", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_project_script_check_runs_script_id"), "project_script_check_runs", ["script_id"])

    if not context.is_offline_mode():
        _migrate_legacy_scripts()


def _migrate_legacy_scripts() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT * FROM project_episode_scripts")).mappings().all()
    for row in rows:
        legacy = [("scene_text", "action"), ("action_notes", "action"), ("dialogue", "dialogue"), ("voiceover", "voiceover")]
        populated = [(name, kind, row.get(name)) for name, kind in legacy if row.get(name) and str(row.get(name)).strip()]
        scenes = []
        if populated:
            scene_id = str(uuid4())
            bind.execute(sa.text("""
                INSERT INTO project_script_scenes
                (id, script_id, title, location, time_of_day, interior_exterior, character_snapshot_ids,
                 auto_duration_seconds, manual_duration_seconds, effective_duration_seconds, story_purpose,
                 sort_order, created_at, updated_at)
                VALUES (:id, :script_id, '待整理场次', '待整理地点', 'other', 'mixed', '[]', 0, NULL, 0, NULL, 0, :created_at, :updated_at)
            """), {"id": scene_id, "script_id": row["id"], "created_at": row["created_at"], "updated_at": row["updated_at"]})
            blocks = []
            for order, (source_field, block_type, content) in enumerate(populated):
                block_id = str(uuid4())
                speaker = "待整理人物" if block_type == "dialogue" else None
                bind.execute(sa.text("""
                    INSERT INTO project_script_blocks
                    (id, scene_id, block_type, character_snapshot_id, temporary_speaker_name, content,
                     emotion, performance_note, sort_order, created_at, updated_at)
                    VALUES (:id, :scene_id, :block_type, NULL, :speaker, :content, NULL, NULL, :sort_order, :created_at, :updated_at)
                """), {
                    "id": block_id, "scene_id": scene_id, "block_type": block_type, "speaker": speaker,
                    "content": str(content).strip(), "sort_order": order,
                    "created_at": row["created_at"], "updated_at": row["updated_at"],
                })
                blocks.append({"id": block_id, "block_type": block_type, "content": str(content).strip(), "sort_order": order, "legacy_source_field": source_field})
            scenes.append({"id": scene_id, "title": "待整理场次", "location": "待整理地点", "time_of_day": "other", "interior_exterior": "mixed", "sort_order": 0, "blocks": blocks})
            bind.execute(sa.text("UPDATE project_episode_scripts SET status = 'needs_review' WHERE id = :id"), {"id": row["id"]})
        snapshot = {
            "id": row["id"], "project_id": row["project_id"], "episode_no": row["episode_no"],
            "version": 1, "revision": 1, "status": "needs_review" if populated else row["status"],
            "scenes": scenes,
            "migration": {"rule_version": 1, "legacy_fields": {name: row.get(name) for name, _ in legacy}},
        }
        bind.execute(sa.text("""
            INSERT INTO project_episode_script_versions
            (id, script_id, version, source_content_version, snapshot, change_source, generation_id, created_at)
            VALUES (:id, :script_id, 1, NULL, :snapshot, 'migration', NULL, :created_at)
        """), {"id": str(uuid4()), "script_id": row["id"], "snapshot": json.dumps(snapshot, ensure_ascii=False, default=str), "created_at": row["updated_at"]})


def downgrade() -> None:
    op.drop_index(op.f("ix_project_script_check_runs_script_id"), table_name="project_script_check_runs")
    op.drop_table("project_script_check_runs")
    for column in ("status", "generation_scope", "episode_no", "project_id"):
        op.drop_index(op.f(f"ix_project_script_generations_{column}"), table_name="project_script_generations")
    op.drop_table("project_script_generations")
    op.drop_index(op.f("ix_project_episode_script_versions_script_id"), table_name="project_episode_script_versions")
    op.drop_table("project_episode_script_versions")
    op.drop_index(op.f("ix_project_script_blocks_character_snapshot_id"), table_name="project_script_blocks")
    op.drop_index(op.f("ix_project_script_blocks_scene_id"), table_name="project_script_blocks")
    op.drop_table("project_script_blocks")
    op.drop_index(op.f("ix_project_script_scenes_script_id"), table_name="project_script_scenes")
    op.drop_table("project_script_scenes")
    for column in ("confirmed_at", "effective_duration_seconds", "manual_duration_seconds", "auto_duration_seconds", "source_content_version", "version", "revision", "title"):
        op.drop_column("project_episode_scripts", column)
