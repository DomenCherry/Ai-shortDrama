"""分集大纲路由模块，管理项目每集大纲的读取和保存。"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import ProjectEpisodeOutlinePayload, ProjectEpisodeOutlineResponse
from app.services.project.story import episode_outlines

router = APIRouter()


@router.get("/{project_id}/episode-outlines", response_model=list[ProjectEpisodeOutlineResponse])
def list_episode_outlines(project_id: str) -> list[dict]:
    """读取项目全部分集大纲。"""
    try:
        return episode_outlines.list_episode_outlines(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/episode-outlines/{episode_no}", response_model=ProjectEpisodeOutlineResponse)
def upsert_episode_outline(project_id: str, episode_no: int, payload: ProjectEpisodeOutlinePayload) -> dict:
    """创建或更新指定集数大纲，并标记后续内容需要复核。"""
    try:
        return episode_outlines.upsert_episode_outline(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
