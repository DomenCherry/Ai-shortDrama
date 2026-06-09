"""项目资产服务模块，处理项目内世界观与角色卡快照的读取、编辑和删除。"""
from typing import Any

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import Project, ProjectCharacterSnapshot, ProjectWorldSnapshot
from app.models.schemas import ProjectCharacterSnapshotUpdate, ProjectWorldSnapshotUpdate
from app.services.project.common import (
    character_snapshot_to_response,
    mark_project_downstream_for_review,
    now_utc,
    world_snapshot_to_response,
)


def list_project_world_snapshots(project_id: str) -> list[dict[str, Any]]:
    """读取项目已加载的世界观快照。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        snapshots = session.scalars(
            select(ProjectWorldSnapshot)
            .where(ProjectWorldSnapshot.project_id == project_id)
            .order_by(ProjectWorldSnapshot.updated_at.desc())
        ).all()
        return [world_snapshot_to_response(snapshot) for snapshot in snapshots]


def delete_project_world_snapshot(project_id: str, snapshot_id: str) -> dict[str, bool]:
    """删除项目内世界观快照，不影响资产库原始世界观。"""
    with get_session() as session:
        snapshot = session.get(ProjectWorldSnapshot, snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise ValueError("项目世界观不存在")
        session.delete(snapshot)
        mark_project_downstream_for_review(session, project_id)
        return {"ok": True}


def update_project_world_snapshot(
    project_id: str,
    snapshot_id: str,
    payload: ProjectWorldSnapshotUpdate,
) -> dict[str, Any]:
    """更新项目内世界观快照，并标记下游故事内容需要复核。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        snapshot = session.get(ProjectWorldSnapshot, snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise ValueError("项目世界观不存在")

        # 项目内微调只更新快照副本，不能回写 WorldBook 或 WorldEntry 原始资产。
        snapshot.name = payload.name
        snapshot.genre = payload.genre
        snapshot.snapshot_content = payload.snapshot_content
        snapshot.entry_snapshot_content = payload.entry_snapshot_content
        snapshot.updated_at = now_utc()
        project.updated_at = snapshot.updated_at
        mark_project_downstream_for_review(session, project_id)
        session.flush()
        return world_snapshot_to_response(snapshot)


def list_project_character_snapshots(project_id: str) -> list[dict[str, Any]]:
    """读取项目已加载的角色卡快照。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        snapshots = session.scalars(
            select(ProjectCharacterSnapshot)
            .where(ProjectCharacterSnapshot.project_id == project_id)
            .order_by(ProjectCharacterSnapshot.updated_at.desc())
        ).all()
        return [character_snapshot_to_response(snapshot) for snapshot in snapshots]


def delete_project_character_snapshot(project_id: str, snapshot_id: str) -> dict[str, bool]:
    """删除项目内角色卡快照，不影响资产库原始角色卡。"""
    with get_session() as session:
        snapshot = session.get(ProjectCharacterSnapshot, snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise ValueError("项目角色不存在")
        session.delete(snapshot)
        mark_project_downstream_for_review(session, project_id)
        return {"ok": True}


def update_project_character_snapshot(
    project_id: str,
    snapshot_id: str,
    payload: ProjectCharacterSnapshotUpdate,
) -> dict[str, Any]:
    """更新项目内角色卡快照，并标记下游故事内容需要复核。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        snapshot = session.get(ProjectCharacterSnapshot, snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise ValueError("项目角色不存在")

        # 项目内微调只更新快照副本，不能回写 CharacterCard 原始资产。
        snapshot.name = payload.name
        snapshot.gender = payload.gender
        snapshot.role_type = payload.role_type
        snapshot.snapshot_content = payload.snapshot_content
        snapshot.visual_description = payload.visual_description
        snapshot.reference_image_url = payload.reference_image_url
        snapshot.reference_local_path = payload.reference_local_path
        snapshot.updated_at = now_utc()
        project.updated_at = snapshot.updated_at
        mark_project_downstream_for_review(session, project_id)
        session.flush()
        return character_snapshot_to_response(snapshot)
