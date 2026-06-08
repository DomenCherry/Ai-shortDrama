from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ProjectCopywritingPayload,
    ProjectCopywritingResponse,
    ProjectStoryboardShotPayload,
    ProjectStoryboardShotResponse,
)
from app.services.project.production import copywriting, storyboard

router = APIRouter()


@router.get("/{project_id}/storyboard-shots/{episode_no}", response_model=list[ProjectStoryboardShotResponse])
def list_storyboard_shots(project_id: str, episode_no: int) -> list[dict]:
    try:
        return storyboard.list_storyboard_shots(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/storyboard-shots/{episode_no}", response_model=ProjectStoryboardShotResponse)
def create_storyboard_shot(project_id: str, episode_no: int, payload: ProjectStoryboardShotPayload) -> dict:
    try:
        return storyboard.create_storyboard_shot(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/storyboard-shots/{episode_no}/{shot_id}", response_model=ProjectStoryboardShotResponse)
def update_storyboard_shot(project_id: str, episode_no: int, shot_id: str, payload: ProjectStoryboardShotPayload) -> dict:
    try:
        return storyboard.update_storyboard_shot(project_id, episode_no, shot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目分镜不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/{project_id}/storyboard-shots/{episode_no}/{shot_id}")
def delete_storyboard_shot(project_id: str, episode_no: int, shot_id: str) -> dict:
    try:
        return storyboard.delete_storyboard_shot(project_id, episode_no, shot_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目分镜不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/copywriting/{episode_no}", response_model=ProjectCopywritingResponse | None)
def get_copywriting(project_id: str, episode_no: int) -> dict | None:
    try:
        return copywriting.get_copywriting(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/copywriting/{episode_no}", response_model=ProjectCopywritingResponse)
def upsert_copywriting(project_id: str, episode_no: int, payload: ProjectCopywritingPayload) -> dict:
    try:
        return copywriting.upsert_copywriting(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
