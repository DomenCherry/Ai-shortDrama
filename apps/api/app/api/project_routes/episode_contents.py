"""单集正文路由模块，管理项目每集详细故事正文的读取和保存。"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import ProjectEpisodeContentPayload, ProjectEpisodeContentResponse
from app.services.project.story import episode_contents

router = APIRouter()


@router.get("/{project_id}/episode-contents/{episode_no}", response_model=ProjectEpisodeContentResponse | None)
def get_episode_content(project_id: str, episode_no: int) -> dict | None:
    """读取指定集数的详细故事正文。"""
    try:
        return episode_contents.get_episode_content(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/episode-contents/{episode_no}", response_model=ProjectEpisodeContentResponse)
def upsert_episode_content(project_id: str, episode_no: int, payload: ProjectEpisodeContentPayload) -> dict:
    """创建或更新指定集数正文，并同步字数和下游复核状态。"""
    try:
        return episode_contents.upsert_episode_content(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
