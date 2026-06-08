from fastapi import APIRouter, HTTPException

from app.models.schemas import ProjectEpisodeScriptPayload, ProjectEpisodeScriptResponse
from app.services.project.story import episode_scripts

router = APIRouter()


@router.get("/{project_id}/episode-scripts/{episode_no}", response_model=ProjectEpisodeScriptResponse | None)
def get_episode_script(project_id: str, episode_no: int) -> dict | None:
    try:
        return episode_scripts.get_episode_script(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/episode-scripts/{episode_no}", response_model=ProjectEpisodeScriptResponse)
def upsert_episode_script(project_id: str, episode_no: int, payload: ProjectEpisodeScriptPayload) -> dict:
    try:
        return episode_scripts.upsert_episode_script(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
