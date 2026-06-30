"""短剧制作路由模块，管理分镜和平台发布文案。"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ProjectCopywritingPayload,
    ProjectCopywritingResponse,
    ProjectStoryboardShotPayload,
    ProjectStoryboardShotResponse,
    ProjectStoryboardResponse,
    ShotVideoGenerationResponse,
    StoryboardDuplicatePayload,
    StoryboardReassignPayload,
    StoryboardReorderPayload,
)
from app.services.project.production import copywriting, shot_videos, storyboard

router = APIRouter()


def _storyboard_status(exc: ValueError) -> int:
    if isinstance(exc, storyboard.StoryboardConflictError):
        return 409
    if str(exc) in {"项目不存在", "项目分镜不存在", "视频生成记录不存在"}:
        return 404
    return 400


@router.get("/{project_id}/storyboards/{episode_no}", response_model=ProjectStoryboardResponse | None)
def get_storyboard(project_id: str, episode_no: int) -> dict | None:
    """读取按剧本场次分组的单集正式分镜。"""
    try:
        return storyboard.get_storyboard(project_id, episode_no)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post("/{project_id}/storyboards/{episode_no}/shots", response_model=ProjectStoryboardShotResponse)
def create_aggregate_shot(project_id: str, episode_no: int, payload: ProjectStoryboardShotPayload) -> dict:
    try:
        return storyboard.create_storyboard_shot(project_id, episode_no, payload)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.put("/{project_id}/storyboards/{episode_no}/shots/{shot_id}", response_model=ProjectStoryboardShotResponse)
def update_aggregate_shot(project_id: str, episode_no: int, shot_id: str, payload: ProjectStoryboardShotPayload) -> dict:
    try:
        return storyboard.update_storyboard_shot(project_id, episode_no, shot_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.delete("/{project_id}/storyboards/{episode_no}/shots/{shot_id}")
def delete_aggregate_shot(project_id: str, episode_no: int, shot_id: str) -> dict:
    try:
        return storyboard.delete_storyboard_shot(project_id, episode_no, shot_id)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post("/{project_id}/storyboards/{episode_no}/scenes/{scene_id}/reorder", response_model=ProjectStoryboardResponse)
def reorder_storyboard_scene(project_id: str, episode_no: int, scene_id: str, payload: StoryboardReorderPayload) -> dict:
    try:
        return storyboard.reorder_storyboard_scene(project_id, episode_no, scene_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post("/{project_id}/storyboards/{episode_no}/scenes/{scene_id}/generate")
async def generate_storyboard_scene(project_id: str, episode_no: int, scene_id: str) -> dict:
    """单场次生成；前端按场次串行调用，可独立重试失败场次。"""
    try:
        return await storyboard.generate_storyboard_scene(project_id, episode_no, scene_id)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post("/{project_id}/storyboards/{episode_no}/shots/{shot_id}/reassign", response_model=ProjectStoryboardShotResponse)
def reassign_storyboard_shot(project_id: str, episode_no: int, shot_id: str, payload: StoryboardReassignPayload) -> dict:
    try:
        return storyboard.reassign_storyboard_shot(project_id, episode_no, shot_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post("/{project_id}/storyboards/{episode_no}/shots/{shot_id}/duplicate", response_model=ProjectStoryboardShotResponse)
def duplicate_storyboard_shot(project_id: str, episode_no: int, shot_id: str, payload: StoryboardDuplicatePayload) -> dict:
    try:
        return storyboard.duplicate_storyboard_shot(project_id, episode_no, shot_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.get(
    "/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations",
    response_model=list[ShotVideoGenerationResponse],
)
def list_shot_video_generations(project_id: str, episode_no: int, shot_id: str) -> list[dict]:
    try:
        return shot_videos.list_video_generations(project_id, episode_no, shot_id)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post(
    "/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations",
    response_model=ShotVideoGenerationResponse,
)
async def create_shot_video_generation(project_id: str, episode_no: int, shot_id: str) -> dict:
    try:
        return await shot_videos.create_video_generation(project_id, episode_no, shot_id)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post(
    "/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/refresh",
    response_model=ShotVideoGenerationResponse,
)
async def refresh_shot_video_generation(project_id: str, episode_no: int, shot_id: str, generation_id: str) -> dict:
    try:
        return await shot_videos.refresh_video_generation(project_id, episode_no, shot_id, generation_id)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post(
    "/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/adopt",
    response_model=ShotVideoGenerationResponse,
)
def adopt_shot_video_generation(project_id: str, episode_no: int, shot_id: str, generation_id: str) -> dict:
    try:
        return shot_videos.adopt_video_generation(project_id, episode_no, shot_id, generation_id)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


@router.post(
    "/{project_id}/storyboards/{episode_no}/shots/{shot_id}/video-generations/{generation_id}/cancel",
    response_model=ShotVideoGenerationResponse,
)
def cancel_shot_video_generation(project_id: str, episode_no: int, shot_id: str, generation_id: str) -> dict:
    try:
        return shot_videos.cancel_video_generation(project_id, episode_no, shot_id, generation_id)
    except ValueError as exc:
        raise HTTPException(status_code=_storyboard_status(exc), detail=str(exc)) from exc


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
