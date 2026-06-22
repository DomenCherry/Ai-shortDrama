"""add scene-grouped storyboard aggregate

Revision ID: 0014_storyboard_aggregate
Revises: 0013_structured_scripts
Create Date: 2026-06-22
"""
import json
from collections import defaultdict
from typing import Sequence, Union
from uuid import uuid4

from alembic import context, op
import sqlalchemy as sa


revision: str = "0014_storyboard_aggregate"
down_revision: Union[str, None] = "0013_structured_scripts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_storyboards",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.String(length=64), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("episode_no", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_script_id", sa.String(length=64), sa.ForeignKey("project_episode_scripts.id"), nullable=True),
        sa.Column("source_script_version", sa.Integer(), nullable=True),
        sa.Column("source_script_status", sa.String(length=24), nullable=True),
        sa.Column("total_duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="draft"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "episode_no", name="uq_project_storyboards_project_episode"),
    )
    op.create_index(op.f("ix_project_storyboards_project_id"), "project_storyboards", ["project_id"])
    op.create_index(op.f("ix_project_storyboards_episode_no"), "project_storyboards", ["episode_no"])
    op.create_index(op.f("ix_project_storyboards_status"), "project_storyboards", ["status"])

    additions = (
        sa.Column("storyboard_id", sa.String(length=64), sa.ForeignKey("project_storyboards.id"), nullable=True),
        sa.Column("source_scene_id", sa.String(length=64), sa.ForeignKey("project_script_scenes.id"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("shot_size", sa.String(length=40), nullable=True),
        sa.Column("subject_description", sa.Text(), nullable=True),
        sa.Column("visual_description", sa.Text(), nullable=True),
        sa.Column("action", sa.Text(), nullable=True),
        sa.Column("camera_angle", sa.Text(), nullable=True),
        sa.Column("camera_movement", sa.Text(), nullable=True),
        sa.Column("composition", sa.Text(), nullable=True),
        sa.Column("character_snapshot_ids", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("expression", sa.Text(), nullable=True),
        sa.Column("environment", sa.Text(), nullable=True),
        sa.Column("props", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("source_block_ids", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("dialogue_snapshot", sa.Text(), nullable=True),
        sa.Column("voiceover_snapshot", sa.Text(), nullable=True),
        sa.Column("sound_effect", sa.Text(), nullable=True),
        sa.Column("music_note", sa.Text(), nullable=True),
        sa.Column("continuity_note", sa.Text(), nullable=True),
        sa.Column("source_status", sa.String(length=24), nullable=False, server_default="unassigned"),
    )
    for column in additions:
        op.add_column("project_storyboard_shots", column)
    op.create_index(op.f("ix_project_storyboard_shots_storyboard_id"), "project_storyboard_shots", ["storyboard_id"])
    op.create_index(op.f("ix_project_storyboard_shots_source_scene_id"), "project_storyboard_shots", ["source_scene_id"])

    op.create_table(
        "project_shot_prompts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("shot_id", sa.String(length=64), sa.ForeignKey("project_storyboard_shots.id"), nullable=False, unique=True),
        sa.Column("source_shot_revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("image_prompt", sa.Text(), nullable=True),
        sa.Column("video_prompt", sa.Text(), nullable=True),
        sa.Column("negative_prompt", sa.Text(), nullable=True),
        sa.Column("first_frame_description", sa.Text(), nullable=True),
        sa.Column("last_frame_description", sa.Text(), nullable=True),
        sa.Column("reference_asset_ids", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("aspect_ratio", sa.String(length=32), nullable=True),
        sa.Column("seedance_prompt", sa.Text(), nullable=True),
        sa.Column("customized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("freshness", sa.String(length=24), nullable=False, server_default="current"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_project_shot_prompts_shot_id"), "project_shot_prompts", ["shot_id"], unique=True)

    if not context.is_offline_mode():
        _migrate_legacy_shots()


def _migrate_legacy_shots() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT * FROM project_storyboard_shots ORDER BY project_id, episode_no, shot_no, created_at"
    )).mappings().all()
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["project_id"], row["episode_no"])].append(row)

    for (project_id, episode_no), shots in grouped.items():
        script = bind.execute(sa.text("""
            SELECT * FROM project_episode_scripts
            WHERE project_id=:project_id AND episode_no=:episode_no
        """), {"project_id": project_id, "episode_no": episode_no}).mappings().first()
        scenes = []
        if script:
            scenes = bind.execute(sa.text("""
                SELECT * FROM project_script_scenes WHERE script_id=:script_id ORDER BY sort_order
            """), {"script_id": script["id"]}).mappings().all()
        storyboard_id = str(uuid4())
        total_duration = sum(float(item["duration_seconds"] or 0) for item in shots)
        timestamp = max(item["updated_at"] for item in shots)
        bind.execute(sa.text("""
            INSERT INTO project_storyboards
            (id, project_id, episode_no, version, revision, source_script_id, source_script_version,
             source_script_status, total_duration_seconds, status, confirmed_at, created_at, updated_at)
            VALUES (:id, :project_id, :episode_no, 1, 1, :script_id, :script_version,
                    :script_status, :duration, 'needs_review', NULL, :created_at, :updated_at)
        """), {
            "id": storyboard_id, "project_id": project_id, "episode_no": episode_no,
            "script_id": script["id"] if script else None,
            "script_version": script["version"] if script else None,
            "script_status": script["status"] if script else None,
            "duration": total_duration, "created_at": shots[0]["created_at"], "updated_at": timestamp,
        })
        scene_orders = defaultdict(int)
        for shot in shots:
            scene = _match_scene(shot.get("scene"), scenes)
            scene_id = scene["id"] if scene else None
            order_key = scene_id or "unassigned"
            sort_order = scene_orders[order_key]
            scene_orders[order_key] += 1
            bind.execute(sa.text("""
                UPDATE project_storyboard_shots
                SET storyboard_id=:storyboard_id, source_scene_id=:scene_id, sort_order=:sort_order,
                    revision=1, shot_size=NULL, subject_description=:subject,
                    visual_description=:visual, action=NULL, camera_angle=:camera,
                    camera_movement=NULL, composition=NULL, character_snapshot_ids='[]', expression=NULL,
                    environment=NULL, props='[]', source_block_ids='[]', dialogue_snapshot=:dialogue,
                    voiceover_snapshot=NULL, sound_effect=NULL, music_note=NULL, continuity_note=NULL,
                    source_status=:source_status, status='needs_review'
                WHERE id=:shot_id
            """), {
                "storyboard_id": storyboard_id, "scene_id": scene_id, "sort_order": sort_order,
                "subject": shot.get("scene"), "visual": shot.get("scene"), "camera": shot.get("camera"),
                "dialogue": shot.get("dialogue_or_voiceover"),
                "source_status": "valid" if scene else "unassigned", "shot_id": shot["id"],
            })
            bind.execute(sa.text("""
                INSERT INTO project_shot_prompts
                (id, shot_id, source_shot_revision, image_prompt, video_prompt, negative_prompt,
                 first_frame_description, last_frame_description, reference_asset_ids, aspect_ratio,
                 seedance_prompt, customized, freshness, updated_at)
                VALUES (:id, :shot_id, 1, :image_prompt, NULL, NULL, NULL, NULL, '[]', NULL,
                        NULL, :customized, 'current', :updated_at)
            """), {
                "id": str(uuid4()), "shot_id": shot["id"], "image_prompt": shot.get("visual_prompt"),
                "customized": bool(shot.get("visual_prompt")), "updated_at": shot["updated_at"],
            })


def _match_scene(scene_text, scenes):
    normalized = (scene_text or "").strip().lower()
    if not normalized:
        return None
    exact = [scene for scene in scenes if normalized in {(scene.get("title") or "").strip().lower(), (scene.get("location") or "").strip().lower()}]
    if len(exact) == 1:
        return exact[0]
    partial = [scene for scene in scenes if any(value and value in normalized for value in ((scene.get("title") or "").strip().lower(), (scene.get("location") or "").strip().lower()))]
    return partial[0] if len(partial) == 1 else None


def downgrade() -> None:
    op.drop_index(op.f("ix_project_shot_prompts_shot_id"), table_name="project_shot_prompts")
    op.drop_table("project_shot_prompts")
    op.drop_index(op.f("ix_project_storyboard_shots_source_scene_id"), table_name="project_storyboard_shots")
    op.drop_index(op.f("ix_project_storyboard_shots_storyboard_id"), table_name="project_storyboard_shots")
    for name in (
        "source_status", "continuity_note", "music_note", "sound_effect", "voiceover_snapshot",
        "dialogue_snapshot", "source_block_ids", "props", "environment", "expression",
        "character_snapshot_ids", "composition", "camera_movement", "camera_angle", "action",
        "visual_description", "subject_description", "shot_size", "revision", "sort_order",
        "source_scene_id", "storyboard_id",
    ):
        op.drop_column("project_storyboard_shots", name)
    op.drop_index(op.f("ix_project_storyboards_status"), table_name="project_storyboards")
    op.drop_index(op.f("ix_project_storyboards_episode_no"), table_name="project_storyboards")
    op.drop_index(op.f("ix_project_storyboards_project_id"), table_name="project_storyboards")
    op.drop_table("project_storyboards")
