"""项目资产路由模块，管理项目内世界观和角色卡快照。"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ProjectCharacterSnapshotResponse,
    ProjectCharacterSnapshotUpdate,
    ProjectWorldSnapshotResponse,
    ProjectWorldSnapshotUpdate,
)
from app.services.project import assets

router = APIRouter()


@router.get("/{project_id}/world-snapshots", response_model=list[ProjectWorldSnapshotResponse])
def list_project_world_snapshots(project_id: str) -> list[dict]:
    """读取项目已加载的世界观快照。"""
    try:
        return assets.list_project_world_snapshots(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}/world-snapshots/{snapshot_id}")
def delete_project_world_snapshot(project_id: str, snapshot_id: str) -> dict:
    """删除项目内世界观快照，不影响资产库原始世界观。"""
    try:
        return assets.delete_project_world_snapshot(project_id, snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/world-snapshots/{snapshot_id}", response_model=ProjectWorldSnapshotResponse)
def update_project_world_snapshot(project_id: str, snapshot_id: str, payload: ProjectWorldSnapshotUpdate) -> dict:
    """更新项目内世界观快照，并标记下游故事内容需要复核。"""
    try:
        return assets.update_project_world_snapshot(project_id, snapshot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目世界观不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/character-snapshots", response_model=list[ProjectCharacterSnapshotResponse])
def list_project_character_snapshots(project_id: str) -> list[dict]:
    """读取项目已加载的角色卡快照。"""
    try:
        return assets.list_project_character_snapshots(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}/character-snapshots/{snapshot_id}")
def delete_project_character_snapshot(project_id: str, snapshot_id: str) -> dict:
    """删除项目内角色卡快照，不影响资产库原始角色卡。"""
    try:
        return assets.delete_project_character_snapshot(project_id, snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/character-snapshots/{snapshot_id}", response_model=ProjectCharacterSnapshotResponse)
def update_project_character_snapshot(project_id: str, snapshot_id: str, payload: ProjectCharacterSnapshotUpdate) -> dict:
    """更新项目内角色卡快照，并标记下游故事内容需要复核。"""
    try:
        return assets.update_project_character_snapshot(project_id, snapshot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目角色不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
