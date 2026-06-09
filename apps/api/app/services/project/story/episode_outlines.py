"""分集大纲服务模块，处理每集大纲的保存、读取和下游状态传播。"""
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import Project, ProjectEpisodeOutline
from app.models.schemas import ProjectEpisodeOutlinePayload
from app.services.project.common import (
    episode_outline_to_response,
    mark_episode_outline_downstream_for_review,
    now_utc,
    validate_episode_no,
)


def list_episode_outlines(project_id: str) -> list[dict[str, Any]]:
    """读取项目全部分集大纲。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        outlines = session.scalars(
            select(ProjectEpisodeOutline)
            .where(ProjectEpisodeOutline.project_id == project_id)
            .order_by(ProjectEpisodeOutline.episode_no.asc())
        ).all()
        return [episode_outline_to_response(outline) for outline in outlines]


def upsert_episode_outline(project_id: str, episode_no: int, payload: ProjectEpisodeOutlinePayload) -> dict[str, Any]:
    """创建或更新指定集数大纲，并标记后续内容需要复核。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        current_time = now_utc()
        outline = session.scalars(
            select(ProjectEpisodeOutline).where(
                ProjectEpisodeOutline.project_id == project_id,
                ProjectEpisodeOutline.episode_no == episode_no,
            )
        ).first()
        if not outline:
            outline = ProjectEpisodeOutline(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=current_time, updated_at=current_time
            )
            session.add(outline)

        outline.title = payload.title
        outline.synopsis = payload.synopsis
        outline.hook = payload.hook
        outline.conflict = payload.conflict
        outline.reversal = payload.reversal
        outline.cliffhanger = payload.cliffhanger
        outline.duration_minutes = payload.duration_minutes
        outline.status = payload.status
        outline.updated_at = current_time
        project.updated_at = current_time
        mark_episode_outline_downstream_for_review(session, project_id, episode_no)
        session.flush()
        return episode_outline_to_response(outline)
