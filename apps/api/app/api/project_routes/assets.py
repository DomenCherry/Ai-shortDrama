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
    try:
        return assets.list_project_world_snapshots(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}/world-snapshots/{snapshot_id}")
def delete_project_world_snapshot(project_id: str, snapshot_id: str) -> dict:
    try:
        return assets.delete_project_world_snapshot(project_id, snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/world-snapshots/{snapshot_id}", response_model=ProjectWorldSnapshotResponse)
def update_project_world_snapshot(project_id: str, snapshot_id: str, payload: ProjectWorldSnapshotUpdate) -> dict:
    try:
        return assets.update_project_world_snapshot(project_id, snapshot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目世界观不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/character-snapshots", response_model=list[ProjectCharacterSnapshotResponse])
def list_project_character_snapshots(project_id: str) -> list[dict]:
    try:
        return assets.list_project_character_snapshots(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}/character-snapshots/{snapshot_id}")
def delete_project_character_snapshot(project_id: str, snapshot_id: str) -> dict:
    try:
        return assets.delete_project_character_snapshot(project_id, snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/character-snapshots/{snapshot_id}", response_model=ProjectCharacterSnapshotResponse)
def update_project_character_snapshot(project_id: str, snapshot_id: str, payload: ProjectCharacterSnapshotUpdate) -> dict:
    try:
        return assets.update_project_character_snapshot(project_id, snapshot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目角色不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
