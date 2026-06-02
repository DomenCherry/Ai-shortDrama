from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update

from app.core.db import get_session
from app.models.db_models import (
    Project,
    ProjectCharacterSnapshot,
    ProjectCopywriting,
    ProjectEpisodeContent,
    ProjectEpisodeOutline,
    ProjectEpisodeScript,
    ProjectStoryboardShot,
    ProjectStoryOutline,
    ProjectWorldSnapshot,
)
from app.models.schemas import (
    ProjectCopywritingPayload,
    ProjectCreate,
    ProjectEpisodeContentPayload,
    ProjectEpisodeOutlinePayload,
    ProjectEpisodeScriptPayload,
    ProjectStoryboardShotPayload,
    ProjectStoryOutlinePayload,
    ProjectUpdate,
)


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


def _world_snapshot_to_response(snapshot: ProjectWorldSnapshot) -> dict[str, Any]:
    return {
        "id": snapshot.id,
        "project_id": snapshot.project_id,
        "source_world_book_id": snapshot.source_world_book_id,
        "source_version": snapshot.source_version,
        "name": snapshot.name,
        "genre": snapshot.genre,
        "snapshot_content": snapshot.snapshot_content,
        "entry_snapshot_content": snapshot.entry_snapshot_content,
        "loaded_at": snapshot.loaded_at.isoformat(),
        "updated_at": snapshot.updated_at.isoformat(),
    }


def _character_snapshot_to_response(snapshot: ProjectCharacterSnapshot) -> dict[str, Any]:
    return {
        "id": snapshot.id,
        "project_id": snapshot.project_id,
        "source_character_card_id": snapshot.source_character_card_id,
        "source_version": snapshot.source_version,
        "name": snapshot.name,
        "gender": snapshot.gender,
        "role_type": snapshot.role_type,
        "snapshot_content": snapshot.snapshot_content,
        "visual_description": snapshot.visual_description,
        "reference_image_url": snapshot.reference_image_url,
        "reference_local_path": snapshot.reference_local_path,
        "loaded_at": snapshot.loaded_at.isoformat(),
        "updated_at": snapshot.updated_at.isoformat(),
    }


def _story_outline_to_response(outline: ProjectStoryOutline) -> dict[str, Any]:
    return {
        "id": outline.id,
        "project_id": outline.project_id,
        "logline": outline.logline,
        "core_conflict": outline.core_conflict,
        "main_goal": outline.main_goal,
        "character_arcs": outline.character_arcs,
        "ending_direction": outline.ending_direction,
        "notes": outline.notes,
        "status": outline.status,
        "created_at": outline.created_at.isoformat(),
        "updated_at": outline.updated_at.isoformat(),
    }


def _episode_outline_to_response(outline: ProjectEpisodeOutline) -> dict[str, Any]:
    return {
        "id": outline.id,
        "project_id": outline.project_id,
        "episode_no": outline.episode_no,
        "title": outline.title,
        "synopsis": outline.synopsis,
        "hook": outline.hook,
        "conflict": outline.conflict,
        "reversal": outline.reversal,
        "cliffhanger": outline.cliffhanger,
        "duration_minutes": outline.duration_minutes,
        "status": outline.status,
        "created_at": outline.created_at.isoformat(),
        "updated_at": outline.updated_at.isoformat(),
    }


def _episode_content_to_response(content: ProjectEpisodeContent) -> dict[str, Any]:
    return {
        "id": content.id,
        "project_id": content.project_id,
        "episode_no": content.episode_no,
        "detailed_content": content.detailed_content,
        "key_beats": content.key_beats,
        "status": content.status,
        "created_at": content.created_at.isoformat(),
        "updated_at": content.updated_at.isoformat(),
    }


def _episode_script_to_response(script: ProjectEpisodeScript) -> dict[str, Any]:
    return {
        "id": script.id,
        "project_id": script.project_id,
        "episode_no": script.episode_no,
        "scene_text": script.scene_text,
        "dialogue": script.dialogue,
        "action_notes": script.action_notes,
        "voiceover": script.voiceover,
        "status": script.status,
        "created_at": script.created_at.isoformat(),
        "updated_at": script.updated_at.isoformat(),
    }


def _storyboard_shot_to_response(shot: ProjectStoryboardShot) -> dict[str, Any]:
    return {
        "id": shot.id,
        "project_id": shot.project_id,
        "episode_no": shot.episode_no,
        "shot_no": shot.shot_no,
        "scene": shot.scene,
        "visual_prompt": shot.visual_prompt,
        "camera": shot.camera,
        "duration_seconds": shot.duration_seconds,
        "dialogue_or_voiceover": shot.dialogue_or_voiceover,
        "status": shot.status,
        "created_at": shot.created_at.isoformat(),
        "updated_at": shot.updated_at.isoformat(),
    }


def _copywriting_to_response(copywriting: ProjectCopywriting) -> dict[str, Any]:
    return {
        "id": copywriting.id,
        "project_id": copywriting.project_id,
        "episode_no": copywriting.episode_no,
        "subtitles": copywriting.subtitles,
        "platform_title": copywriting.platform_title,
        "platform_description": copywriting.platform_description,
        "publish_copy": copywriting.publish_copy,
        "status": copywriting.status,
        "created_at": copywriting.created_at.isoformat(),
        "updated_at": copywriting.updated_at.isoformat(),
    }


def _validate_total_duration(episode_count: int, episode_duration: float) -> float:
    total_duration = episode_count * episode_duration
    if total_duration > 240:
        raise ValueError("总时长不能超过 240 分钟，请减少集数或单集时长")
    return total_duration


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_idea(value: str) -> str:
    idea = value.strip()
    if not idea:
        raise ValueError("请先输入短剧创意描述")
    return idea


def _validate_episode_no(project: Project, episode_no: int) -> None:
    if episode_no <= 0 or episode_no > project.episode_count:
        raise ValueError("集数编号必须在项目集数范围内")


def _mark_project_downstream_for_review(session, project_id: str) -> None:
    now = _now()
    for model in (
        ProjectStoryOutline,
        ProjectEpisodeOutline,
        ProjectEpisodeContent,
        ProjectEpisodeScript,
        ProjectStoryboardShot,
        ProjectCopywriting,
    ):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.status != "needs_review")
            .values(status="needs_review", updated_at=now)
        )


def _mark_story_downstream_for_review(session, project_id: str) -> None:
    now = _now()
    for model in (ProjectEpisodeOutline, ProjectEpisodeContent, ProjectEpisodeScript, ProjectStoryboardShot, ProjectCopywriting):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.status != "needs_review")
            .values(status="needs_review", updated_at=now)
        )


def _mark_episode_outline_downstream_for_review(session, project_id: str, episode_no: int) -> None:
    now = _now()
    for model in (ProjectEpisodeContent, ProjectEpisodeScript, ProjectStoryboardShot, ProjectCopywriting):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.episode_no == episode_no, model.status != "needs_review")
            .values(status="needs_review", updated_at=now)
        )


def _mark_episode_content_downstream_for_review(session, project_id: str, episode_no: int) -> None:
    now = _now()
    for model in (ProjectEpisodeScript, ProjectStoryboardShot, ProjectCopywriting):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.episode_no == episode_no, model.status != "needs_review")
            .values(status="needs_review", updated_at=now)
        )


def _mark_script_downstream_for_review(session, project_id: str, episode_no: int) -> None:
    now = _now()
    for model in (ProjectStoryboardShot, ProjectCopywriting):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.episode_no == episode_no, model.status != "needs_review")
            .values(status="needs_review", updated_at=now)
        )


def list_projects() -> list[dict[str, Any]]:
    with get_session() as session:
        projects = session.scalars(select(Project).order_by(Project.updated_at.desc())).all()
        return [_project_to_response(project) for project in projects]


def get_project(project_id: str) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        return _project_to_response(project)


def create_project(payload: ProjectCreate) -> dict[str, Any]:
    total_duration = _validate_total_duration(payload.episode_count, payload.episode_duration)

    now = _now()
    project = Project(
        id=str(uuid4()),
        title=_normalize_optional_text(payload.title) or "未命名短剧",
        idea=_normalize_idea(payload.idea),
        target_platform=_normalize_optional_text(payload.target_platform),
        genre=_normalize_optional_text(payload.genre),
        episode_count=payload.episode_count,
        episode_duration=payload.episode_duration,
        total_duration=total_duration,
        target_audience=_normalize_optional_text(payload.target_audience),
        style=_normalize_optional_text(payload.style),
        remark=_normalize_optional_text(payload.remark),
        status="draft",
        created_at=now,
        updated_at=now,
    )

    with get_session() as session:
        session.add(project)
        session.flush()
        return _project_to_response(project)


def update_project(project_id: str, payload: ProjectUpdate) -> dict[str, Any]:
    total_duration = _validate_total_duration(payload.episode_count, payload.episode_duration)

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        project.title = _normalize_optional_text(payload.title) or "未命名短剧"
        project.idea = _normalize_idea(payload.idea)
        project.target_platform = _normalize_optional_text(payload.target_platform)
        project.genre = _normalize_optional_text(payload.genre)
        project.episode_count = payload.episode_count
        project.episode_duration = payload.episode_duration
        project.total_duration = total_duration
        project.target_audience = _normalize_optional_text(payload.target_audience)
        project.style = _normalize_optional_text(payload.style)
        project.remark = _normalize_optional_text(payload.remark)
        project.updated_at = _now()
        _mark_project_downstream_for_review(session, project_id)

        session.flush()
        return _project_to_response(project)


def list_project_world_snapshots(project_id: str) -> list[dict[str, Any]]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        snapshots = session.scalars(
            select(ProjectWorldSnapshot)
            .where(ProjectWorldSnapshot.project_id == project_id)
            .order_by(ProjectWorldSnapshot.updated_at.desc())
        ).all()
        return [_world_snapshot_to_response(snapshot) for snapshot in snapshots]


def delete_project_world_snapshot(project_id: str, snapshot_id: str) -> dict[str, bool]:
    with get_session() as session:
        snapshot = session.get(ProjectWorldSnapshot, snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise ValueError("项目世界观不存在")
        session.delete(snapshot)
        _mark_project_downstream_for_review(session, project_id)
        return {"ok": True}


def list_project_character_snapshots(project_id: str) -> list[dict[str, Any]]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        snapshots = session.scalars(
            select(ProjectCharacterSnapshot)
            .where(ProjectCharacterSnapshot.project_id == project_id)
            .order_by(ProjectCharacterSnapshot.updated_at.desc())
        ).all()
        return [_character_snapshot_to_response(snapshot) for snapshot in snapshots]


def delete_project_character_snapshot(project_id: str, snapshot_id: str) -> dict[str, bool]:
    with get_session() as session:
        snapshot = session.get(ProjectCharacterSnapshot, snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise ValueError("项目角色不存在")
        session.delete(snapshot)
        _mark_project_downstream_for_review(session, project_id)
        return {"ok": True}


def get_story_outline(project_id: str) -> dict[str, Any] | None:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        return _story_outline_to_response(outline) if outline else None


def upsert_story_outline(project_id: str, payload: ProjectStoryOutlinePayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        now = _now()
        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        if not outline:
            outline = ProjectStoryOutline(id=str(uuid4()), project_id=project_id, created_at=now, updated_at=now)
            session.add(outline)

        outline.logline = payload.logline
        outline.core_conflict = payload.core_conflict
        outline.main_goal = payload.main_goal
        outline.character_arcs = payload.character_arcs
        outline.ending_direction = payload.ending_direction
        outline.notes = payload.notes
        outline.status = payload.status
        outline.updated_at = now
        project.updated_at = now
        _mark_story_downstream_for_review(session, project_id)
        session.flush()
        return _story_outline_to_response(outline)


def list_episode_outlines(project_id: str) -> list[dict[str, Any]]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        outlines = session.scalars(
            select(ProjectEpisodeOutline)
            .where(ProjectEpisodeOutline.project_id == project_id)
            .order_by(ProjectEpisodeOutline.episode_no.asc())
        ).all()
        return [_episode_outline_to_response(outline) for outline in outlines]


def upsert_episode_outline(project_id: str, episode_no: int, payload: ProjectEpisodeOutlinePayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        now = _now()
        outline = session.scalars(
            select(ProjectEpisodeOutline).where(
                ProjectEpisodeOutline.project_id == project_id,
                ProjectEpisodeOutline.episode_no == episode_no,
            )
        ).first()
        if not outline:
            outline = ProjectEpisodeOutline(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=now, updated_at=now
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
        outline.updated_at = now
        project.updated_at = now
        _mark_episode_outline_downstream_for_review(session, project_id, episode_no)
        session.flush()
        return _episode_outline_to_response(outline)


def get_episode_content(project_id: str, episode_no: int) -> dict[str, Any] | None:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        content = session.scalars(
            select(ProjectEpisodeContent).where(
                ProjectEpisodeContent.project_id == project_id,
                ProjectEpisodeContent.episode_no == episode_no,
            )
        ).first()
        return _episode_content_to_response(content) if content else None


def upsert_episode_content(project_id: str, episode_no: int, payload: ProjectEpisodeContentPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        now = _now()
        content = session.scalars(
            select(ProjectEpisodeContent).where(
                ProjectEpisodeContent.project_id == project_id,
                ProjectEpisodeContent.episode_no == episode_no,
            )
        ).first()
        if not content:
            content = ProjectEpisodeContent(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=now, updated_at=now
            )
            session.add(content)

        content.detailed_content = payload.detailed_content
        content.key_beats = payload.key_beats
        content.status = payload.status
        content.updated_at = now
        project.updated_at = now
        _mark_episode_content_downstream_for_review(session, project_id, episode_no)
        session.flush()
        return _episode_content_to_response(content)


def get_episode_script(project_id: str, episode_no: int) -> dict[str, Any] | None:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        script = session.scalars(
            select(ProjectEpisodeScript).where(
                ProjectEpisodeScript.project_id == project_id,
                ProjectEpisodeScript.episode_no == episode_no,
            )
        ).first()
        return _episode_script_to_response(script) if script else None


def upsert_episode_script(project_id: str, episode_no: int, payload: ProjectEpisodeScriptPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        now = _now()
        script = session.scalars(
            select(ProjectEpisodeScript).where(
                ProjectEpisodeScript.project_id == project_id,
                ProjectEpisodeScript.episode_no == episode_no,
            )
        ).first()
        if not script:
            script = ProjectEpisodeScript(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=now, updated_at=now
            )
            session.add(script)

        script.scene_text = payload.scene_text
        script.dialogue = payload.dialogue
        script.action_notes = payload.action_notes
        script.voiceover = payload.voiceover
        script.status = payload.status
        script.updated_at = now
        project.updated_at = now
        _mark_script_downstream_for_review(session, project_id, episode_no)
        session.flush()
        return _episode_script_to_response(script)


def list_storyboard_shots(project_id: str, episode_no: int) -> list[dict[str, Any]]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        shots = session.scalars(
            select(ProjectStoryboardShot)
            .where(ProjectStoryboardShot.project_id == project_id, ProjectStoryboardShot.episode_no == episode_no)
            .order_by(ProjectStoryboardShot.shot_no.asc(), ProjectStoryboardShot.updated_at.asc())
        ).all()
        return [_storyboard_shot_to_response(shot) for shot in shots]


def create_storyboard_shot(project_id: str, episode_no: int, payload: ProjectStoryboardShotPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        now = _now()
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
            created_at=now,
            updated_at=now,
        )
        project.updated_at = now
        session.add(shot)
        session.flush()
        return _storyboard_shot_to_response(shot)


def update_storyboard_shot(
    project_id: str, episode_no: int, shot_id: str, payload: ProjectStoryboardShotPayload
) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        shot = session.get(ProjectStoryboardShot, shot_id)
        if not shot or shot.project_id != project_id or shot.episode_no != episode_no:
            raise ValueError("项目分镜不存在")

        now = _now()
        shot.shot_no = payload.shot_no
        shot.scene = payload.scene
        shot.visual_prompt = payload.visual_prompt
        shot.camera = payload.camera
        shot.duration_seconds = payload.duration_seconds
        shot.dialogue_or_voiceover = payload.dialogue_or_voiceover
        shot.status = payload.status
        shot.updated_at = now
        project.updated_at = now
        session.flush()
        return _storyboard_shot_to_response(shot)


def delete_storyboard_shot(project_id: str, episode_no: int, shot_id: str) -> dict[str, bool]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        shot = session.get(ProjectStoryboardShot, shot_id)
        if not shot or shot.project_id != project_id or shot.episode_no != episode_no:
            raise ValueError("项目分镜不存在")

        project.updated_at = _now()
        session.delete(shot)
        return {"ok": True}


def get_copywriting(project_id: str, episode_no: int) -> dict[str, Any] | None:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        copywriting = session.scalars(
            select(ProjectCopywriting).where(
                ProjectCopywriting.project_id == project_id,
                ProjectCopywriting.episode_no == episode_no,
            )
        ).first()
        return _copywriting_to_response(copywriting) if copywriting else None


def upsert_copywriting(project_id: str, episode_no: int, payload: ProjectCopywritingPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        _validate_episode_no(project, episode_no)

        now = _now()
        copywriting = session.scalars(
            select(ProjectCopywriting).where(
                ProjectCopywriting.project_id == project_id,
                ProjectCopywriting.episode_no == episode_no,
            )
        ).first()
        if not copywriting:
            copywriting = ProjectCopywriting(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=now, updated_at=now
            )
            session.add(copywriting)

        copywriting.subtitles = payload.subtitles
        copywriting.platform_title = payload.platform_title
        copywriting.platform_description = payload.platform_description
        copywriting.publish_copy = payload.publish_copy
        copywriting.status = payload.status
        copywriting.updated_at = now
        project.updated_at = now
        session.flush()
        return _copywriting_to_response(copywriting)
