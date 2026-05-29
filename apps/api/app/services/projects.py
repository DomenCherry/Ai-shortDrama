from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import Project
from app.models.schemas import ProjectCreate


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _project_to_response(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "title": project.title,
        "idea": project.idea,
        "target_platform": project.target_platform,
        "genre": project.genre,
        "episode_count": project.episode_count,
        "episode_duration": project.episode_duration,
        "total_duration": project.total_duration,
        "target_audience": project.target_audience,
        "style": project.style,
        "remark": project.remark,
        "status": project.status,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def list_projects() -> list[dict[str, Any]]:
    with get_session() as session:
        projects = session.scalars(select(Project).order_by(Project.updated_at.desc())).all()
        return [_project_to_response(project) for project in projects]


def create_project(payload: ProjectCreate) -> dict[str, Any]:
    total_duration = payload.episode_count * payload.episode_duration
    if total_duration > 240:
        raise ValueError("总时长不能超过 240 分钟，请减少集数或单集时长")

    now = _now()
    project = Project(
        id=str(uuid4()),
        title=payload.title.strip() if payload.title else "未命名短剧",
        idea=payload.idea.strip(),
        target_platform=payload.target_platform,
        genre=payload.genre,
        episode_count=payload.episode_count,
        episode_duration=payload.episode_duration,
        total_duration=total_duration,
        target_audience=payload.target_audience,
        style=payload.style,
        remark=payload.remark,
        status="draft",
        created_at=now,
        updated_at=now,
    )

    with get_session() as session:
        session.add(project)
        session.flush()
        return _project_to_response(project)
