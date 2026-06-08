from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import Project
from app.models.schemas import ProjectCreate, ProjectUpdate
from app.services.project.common import (
    mark_project_downstream_for_review,
    normalize_optional_text,
    now_utc,
    project_to_response,
)


def validate_total_duration(episode_count: int, episode_duration: float) -> float:
    total_duration = episode_count * episode_duration
    if total_duration > 240:
        raise ValueError("总时长不能超过 240 分钟，请减少集数或单集时长")
    return total_duration


def normalize_idea(value: str) -> str:
    idea = value.strip()
    if not idea:
        raise ValueError("请先输入短剧创意描述")
    return idea


def list_projects() -> list[dict[str, Any]]:
    with get_session() as session:
        projects = session.scalars(select(Project).order_by(Project.updated_at.desc())).all()
        return [project_to_response(project) for project in projects]


def get_project(project_id: str) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        return project_to_response(project)


def create_project(payload: ProjectCreate) -> dict[str, Any]:
    total_duration = validate_total_duration(payload.episode_count, payload.episode_duration)

    current_time = now_utc()
    project = Project(
        id=str(uuid4()),
        title=normalize_optional_text(payload.title) or "未命名短剧",
        idea=normalize_idea(payload.idea),
        target_platform=normalize_optional_text(payload.target_platform),
        genre=normalize_optional_text(payload.genre),
        episode_count=payload.episode_count,
        episode_duration=payload.episode_duration,
        total_duration=total_duration,
        target_audience=normalize_optional_text(payload.target_audience),
        style=normalize_optional_text(payload.style),
        remark=normalize_optional_text(payload.remark),
        status="draft",
        created_at=current_time,
        updated_at=current_time,
    )

    with get_session() as session:
        session.add(project)
        session.flush()
        return project_to_response(project)


def update_project(project_id: str, payload: ProjectUpdate) -> dict[str, Any]:
    total_duration = validate_total_duration(payload.episode_count, payload.episode_duration)

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        project.title = normalize_optional_text(payload.title) or "未命名短剧"
        project.idea = normalize_idea(payload.idea)
        project.target_platform = normalize_optional_text(payload.target_platform)
        project.genre = normalize_optional_text(payload.genre)
        project.episode_count = payload.episode_count
        project.episode_duration = payload.episode_duration
        project.total_duration = total_duration
        project.target_audience = normalize_optional_text(payload.target_audience)
        project.style = normalize_optional_text(payload.style)
        project.remark = normalize_optional_text(payload.remark)
        project.updated_at = now_utc()

        # 项目基础设定变化会影响所有下游创作内容，统一标记为需要检查。
        mark_project_downstream_for_review(session, project_id)

        session.flush()
        return project_to_response(project)
