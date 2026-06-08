from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import Project, ProjectEpisodeScript
from app.models.schemas import ProjectEpisodeScriptPayload
from app.services.project.common import (
    episode_script_to_response,
    mark_script_downstream_for_review,
    now_utc,
    validate_episode_no,
)


def get_episode_script(project_id: str, episode_no: int) -> dict[str, Any] | None:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        script = session.scalars(
            select(ProjectEpisodeScript).where(
                ProjectEpisodeScript.project_id == project_id,
                ProjectEpisodeScript.episode_no == episode_no,
            )
        ).first()
        return episode_script_to_response(script) if script else None


def upsert_episode_script(project_id: str, episode_no: int, payload: ProjectEpisodeScriptPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        current_time = now_utc()
        script = session.scalars(
            select(ProjectEpisodeScript).where(
                ProjectEpisodeScript.project_id == project_id,
                ProjectEpisodeScript.episode_no == episode_no,
            )
        ).first()
        if not script:
            script = ProjectEpisodeScript(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=current_time, updated_at=current_time
            )
            session.add(script)

        script.scene_text = payload.scene_text
        script.dialogue = payload.dialogue
        script.action_notes = payload.action_notes
        script.voiceover = payload.voiceover
        script.status = payload.status
        script.updated_at = current_time
        project.updated_at = current_time
        mark_script_downstream_for_review(session, project_id, episode_no)
        session.flush()
        return episode_script_to_response(script)
