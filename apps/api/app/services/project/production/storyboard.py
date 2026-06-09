"""分镜服务模块，处理单集分镜镜头的列表、新增、编辑和删除。"""
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import Project, ProjectStoryboardShot
from app.models.schemas import ProjectStoryboardShotPayload
from app.services.project.common import now_utc, storyboard_shot_to_response, validate_episode_no


def list_storyboard_shots(project_id: str, episode_no: int) -> list[dict[str, Any]]:
    """读取指定集数的分镜镜头列表。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        shots = session.scalars(
            select(ProjectStoryboardShot)
            .where(ProjectStoryboardShot.project_id == project_id, ProjectStoryboardShot.episode_no == episode_no)
            .order_by(ProjectStoryboardShot.shot_no.asc(), ProjectStoryboardShot.updated_at.asc())
        ).all()
        return [storyboard_shot_to_response(shot) for shot in shots]


def create_storyboard_shot(project_id: str, episode_no: int, payload: ProjectStoryboardShotPayload) -> dict[str, Any]:
    """创建单个分镜镜头，并校验所属项目和集数。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        current_time = now_utc()
        shot = ProjectStoryboardShot(
            id=str(uuid4()),
            project_id=project_id,
            episode_no=episode_no,
            shot_no=payload.shot_no,
            scene=payload.scene,
            visual_prompt=payload.visual_prompt,
            camera=payload.camera,
            duration_seconds=payload.duration_seconds,
            dialogue_or_voiceover=payload.dialogue_or_voiceover,
            status=payload.status,
            created_at=current_time,
            updated_at=current_time,
        )
        project.updated_at = current_time
        session.add(shot)
        session.flush()
        return storyboard_shot_to_response(shot)


def update_storyboard_shot(
    project_id: str, episode_no: int, shot_id: str, payload: ProjectStoryboardShotPayload
) -> dict[str, Any]:
    """更新单个分镜镜头，确保镜头归属当前项目和集数。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        shot = session.get(ProjectStoryboardShot, shot_id)
        if not shot or shot.project_id != project_id or shot.episode_no != episode_no:
            raise ValueError("项目分镜不存在")

        current_time = now_utc()
        shot.shot_no = payload.shot_no
        shot.scene = payload.scene
        shot.visual_prompt = payload.visual_prompt
        shot.camera = payload.camera
        shot.duration_seconds = payload.duration_seconds
        shot.dialogue_or_voiceover = payload.dialogue_or_voiceover
        shot.status = payload.status
        shot.updated_at = current_time
        project.updated_at = current_time
        session.flush()
        return storyboard_shot_to_response(shot)


def delete_storyboard_shot(project_id: str, episode_no: int, shot_id: str) -> dict[str, bool]:
    """删除单个分镜镜头，只影响当前项目当前集。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        shot = session.get(ProjectStoryboardShot, shot_id)
        if not shot or shot.project_id != project_id or shot.episode_no != episode_no:
            raise ValueError("项目分镜不存在")

        project.updated_at = now_utc()
        session.delete(shot)
        return {"ok": True}
