"""短剧制作路由模块，管理分镜和平台发布文案。"""
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
    """读取指定集数的分镜镜头列表。"""
    try:
        return storyboard.list_storyboard_shots(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/storyboard-shots/{episode_no}", response_model=ProjectStoryboardShotResponse)
def create_storyboard_shot(project_id: str, episode_no: int, payload: ProjectStoryboardShotPayload) -> dict:
    """创建单个分镜镜头，并校验所属项目和集数。"""
    try:
        return storyboard.create_storyboard_shot(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/storyboard-shots/{episode_no}/{shot_id}", response_model=ProjectStoryboardShotResponse)
def update_storyboard_shot(project_id: str, episode_no: int, shot_id: str, payload: ProjectStoryboardShotPayload) -> dict:
    """更新单个分镜镜头，确保镜头归属当前项目和集数。"""
    try:
        return storyboard.update_storyboard_shot(project_id, episode_no, shot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目分镜不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/{project_id}/storyboard-shots/{episode_no}/{shot_id}")
def delete_storyboard_shot(project_id: str, episode_no: int, shot_id: str) -> dict:
    """删除单个分镜镜头，只影响当前项目当前集。"""
    try:
        return storyboard.delete_storyboard_shot(project_id, episode_no, shot_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目分镜不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/copywriting/{episode_no}", response_model=ProjectCopywritingResponse | None)
def get_copywriting(project_id: str, episode_no: int) -> dict | None:
    """读取指定集数的字幕和平台发布文案。"""
    try:
        return copywriting.get_copywriting(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/copywriting/{episode_no}", response_model=ProjectCopywritingResponse)
def upsert_copywriting(project_id: str, episode_no: int, payload: ProjectCopywritingPayload) -> dict:
    """创建或更新指定集数的字幕和平台发布文案。"""
    try:
        return copywriting.upsert_copywriting(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
