from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import Project, ProjectCopywriting
from app.models.schemas import ProjectCopywritingPayload
from app.services.project.common import copywriting_to_response, now_utc, validate_episode_no


def get_copywriting(project_id: str, episode_no: int) -> dict[str, Any] | None:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        copywriting = session.scalars(
            select(ProjectCopywriting).where(
                ProjectCopywriting.project_id == project_id,
                ProjectCopywriting.episode_no == episode_no,
            )
        ).first()
        return copywriting_to_response(copywriting) if copywriting else None


def upsert_copywriting(project_id: str, episode_no: int, payload: ProjectCopywritingPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        current_time = now_utc()
        copywriting = session.scalars(
            select(ProjectCopywriting).where(
                ProjectCopywriting.project_id == project_id,
                ProjectCopywriting.episode_no == episode_no,
            )
        ).first()
        if not copywriting:
            copywriting = ProjectCopywriting(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=current_time, updated_at=current_time
            )
            session.add(copywriting)

        copywriting.subtitles = payload.subtitles
        copywriting.platform_title = payload.platform_title
        copywriting.platform_description = payload.platform_description
        copywriting.publish_copy = payload.publish_copy
        copywriting.status = payload.status
        copywriting.updated_at = current_time
        project.updated_at = current_time
        session.flush()
        return copywriting_to_response(copywriting)
