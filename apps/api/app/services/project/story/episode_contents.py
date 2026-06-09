"""单集正文服务模块，处理每集详细故事正文保存、读取和字数统计。"""
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import Project, ProjectEpisodeContent
from app.models.schemas import ProjectEpisodeContentPayload
from app.services.project.common import (
    count_content_characters,
    episode_content_to_response,
    mark_episode_content_downstream_for_review,
    now_utc,
    validate_episode_no,
)


def get_episode_content(project_id: str, episode_no: int) -> dict[str, Any] | None:
    """读取指定集数的详细故事正文。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        content = session.scalars(
            select(ProjectEpisodeContent).where(
                ProjectEpisodeContent.project_id == project_id,
                ProjectEpisodeContent.episode_no == episode_no,
            )
        ).first()
        return episode_content_to_response(content) if content else None


def upsert_episode_content(project_id: str, episode_no: int, payload: ProjectEpisodeContentPayload) -> dict[str, Any]:
    """创建或更新指定集数正文，并同步字数和下游复核状态。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        current_time = now_utc()
        content = session.scalars(
            select(ProjectEpisodeContent).where(
                ProjectEpisodeContent.project_id == project_id,
                ProjectEpisodeContent.episode_no == episode_no,
            )
        ).first()
        if not content:
            content = ProjectEpisodeContent(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=current_time, updated_at=current_time
            )
            session.add(content)

        content.title = payload.title
        content.detailed_content = payload.detailed_content
        content.chapter_summary = payload.chapter_summary
        content.hook = payload.hook
        content.key_beats = payload.key_beats
        content.word_count = count_content_characters(payload.detailed_content)
        content.previous_context_summary = payload.previous_context_summary
        content.quality_check_notes = payload.quality_check_notes
        content.status = payload.status
        content.updated_at = current_time
        project.updated_at = current_time
        mark_episode_content_downstream_for_review(session, project_id, episode_no)
        session.flush()
        return episode_content_to_response(content)
