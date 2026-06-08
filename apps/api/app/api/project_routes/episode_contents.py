from fastapi import APIRouter, HTTPException

from app.models.schemas import ProjectEpisodeContentPayload, ProjectEpisodeContentResponse
from app.services.project.story import episode_contents

router = APIRouter()


@router.get("/{project_id}/episode-contents/{episode_no}", response_model=ProjectEpisodeContentResponse | None)
def get_episode_content(project_id: str, episode_no: int) -> dict | None:
    try:
        return episode_contents.get_episode_content(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/episode-contents/{episode_no}", response_model=ProjectEpisodeContentResponse)
def upsert_episode_content(project_id: str, episode_no: int, payload: ProjectEpisodeContentPayload) -> dict:
    try:
        return episode_contents.upsert_episode_content(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
