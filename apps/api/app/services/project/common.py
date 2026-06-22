"""项目通用服务模块，提供序列化、校验、时间和下游内容状态传播能力。"""
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import update

from app.models.db_models import (
    Project,
    ProjectCharacterSnapshot,
    ProjectCopywriting,
    EpisodeContentGenerationVersion,
    ProjectEpisodeContent,
    ProjectEpisodeOutline,
    ProjectEpisodeScript,
    ProjectStoryboardShot,
    ProjectStoryOutline,
    ProjectWorldSnapshot,
)


def now_utc() -> datetime:
    """返回带 UTC 时区的当前时间，供项目模块统一写入时间字段。"""
    return datetime.now(timezone.utc)


def project_to_response(project: Project) -> dict[str, Any]:
    """将项目模型转换为 API 响应结构。"""
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


def world_snapshot_to_response(snapshot: ProjectWorldSnapshot) -> dict[str, Any]:
    """将项目世界观快照转换为 API 响应结构。"""
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


def character_snapshot_to_response(snapshot: ProjectCharacterSnapshot) -> dict[str, Any]:
    """将项目角色卡快照转换为 API 响应结构。"""
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


def story_outline_to_response(outline: ProjectStoryOutline) -> dict[str, Any]:
    """将故事大纲模型转换为 API 响应结构。"""
    return {
        "id": outline.id,
        "project_id": outline.project_id,
        "logline": outline.logline,
        "story_background": outline.story_background,
        "core_conflict": outline.core_conflict,
        "main_goal": outline.main_goal,
        "story_start": outline.story_start,
        "plot_structure": outline.plot_structure,
        "reversals": outline.reversals,
        "emotion_curve": outline.emotion_curve,
        "foreshadowing": outline.foreshadowing,
        "character_arcs": outline.character_arcs,
        "ending_direction": outline.ending_direction,
        "pacing_advice": outline.pacing_advice,
        "capacity_advice": outline.capacity_advice,
        "notes": outline.notes,
        "status": outline.status,
        "created_at": outline.created_at.isoformat(),
        "updated_at": outline.updated_at.isoformat(),
    }


def episode_outline_to_response(outline: ProjectEpisodeOutline) -> dict[str, Any]:
    """将分集大纲模型转换为 API 响应结构。"""
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


def episode_content_to_response(content: ProjectEpisodeContent) -> dict[str, Any]:
    """将单集正文模型转换为 API 响应结构。"""
    return {
        "id": content.id,
        "project_id": content.project_id,
        "episode_no": content.episode_no,
        "title": content.title,
        "detailed_content": content.detailed_content,
        "chapter_summary": content.chapter_summary,
        "hook": content.hook,
        "key_beats": content.key_beats,
        "word_count": content.word_count,
        "previous_context_summary": content.previous_context_summary,
        "quality_check_notes": content.quality_check_notes,
        "status": content.status,
        "created_at": content.created_at.isoformat(),
        "updated_at": content.updated_at.isoformat(),
    }


def episode_content_generation_to_response(generation: EpisodeContentGenerationVersion) -> dict[str, Any]:
    """将单集正文候选版本转换为 API 响应结构。"""
    try:
        input_snapshot = json.loads(generation.input_snapshot)
    except json.JSONDecodeError:
        input_snapshot = {}
    return {
        "id": generation.id,
        "project_id": generation.project_id,
        "episode_no": generation.episode_no,
        "instruction": generation.instruction,
        "input_snapshot": input_snapshot if isinstance(input_snapshot, dict) else {},
        "output_text": generation.output_text,
        "word_count": count_content_characters(generation.output_text),
        "status": generation.status,
        "client_request_id": generation.client_request_id,
        "model_config_id": generation.model_config_id,
        "model_name": generation.model_name,
        "elapsed_ms": generation.elapsed_ms,
        "created_at": generation.created_at.isoformat(),
        "updated_at": generation.updated_at.isoformat(),
        "adopted_at": generation.adopted_at.isoformat() if generation.adopted_at else None,
    }


def episode_script_to_response(script: ProjectEpisodeScript) -> dict[str, Any]:
    """将单集剧本模型转换为 API 响应结构。"""
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


def storyboard_shot_to_response(shot: ProjectStoryboardShot) -> dict[str, Any]:
    """将分镜镜头模型转换为 API 响应结构。"""
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


def copywriting_to_response(copywriting: ProjectCopywriting) -> dict[str, Any]:
    """将发布文案模型转换为 API 响应结构。"""
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


def normalize_optional_text(value: str | None) -> str | None:
    """把空字符串统一归一为 None，避免数据库保存无意义空白。"""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def validate_episode_no(project: Project, episode_no: int) -> None:
    """校验集数编号是否在当前项目范围内。"""
    if episode_no <= 0 or episode_no > project.episode_count:
        raise ValueError("集数编号必须在项目集数范围内")


def count_content_characters(content: str | None) -> int:
    """统计非空白字符数量，用于正文规模评估。"""
    if not content:
        return 0
    return sum(1 for char in content if not char.isspace())


def mark_project_downstream_for_review(session, project_id: str) -> None:
    """项目基础设定变化后，标记所有下游内容需要复核。"""
    current_time = now_utc()
    for model in (
        ProjectStoryOutline,
        ProjectEpisodeOutline,
        ProjectEpisodeContent,
        ProjectStoryboardShot,
        ProjectCopywriting,
    ):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.status != "needs_review")
            .values(status="needs_review", updated_at=current_time)
        )
    _mark_scripts_for_review(session, ProjectEpisodeScript.project_id == project_id, current_time)


def mark_story_downstream_for_review(session, project_id: str) -> None:
    """故事大纲变化后，标记分集、正文、剧本和制作内容需要复核。"""
    current_time = now_utc()
    for model in (ProjectEpisodeOutline, ProjectEpisodeContent, ProjectStoryboardShot, ProjectCopywriting):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.status != "needs_review")
            .values(status="needs_review", updated_at=current_time)
        )
    _mark_scripts_for_review(session, ProjectEpisodeScript.project_id == project_id, current_time)


def mark_episode_outline_downstream_for_review(session, project_id: str, episode_no: int) -> None:
    """分集大纲变化后，标记对应单集的后续内容需要复核。"""
    current_time = now_utc()
    for model in (ProjectEpisodeContent, ProjectStoryboardShot, ProjectCopywriting):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.episode_no == episode_no, model.status != "needs_review")
            .values(status="needs_review", updated_at=current_time)
        )
    _mark_scripts_for_review(
        session,
        (ProjectEpisodeScript.project_id == project_id) & (ProjectEpisodeScript.episode_no == episode_no),
        current_time,
    )


def mark_episode_content_downstream_for_review(session, project_id: str, episode_no: int) -> None:
    """单集正文变化后，标记剧本和制作内容需要复核。"""
    current_time = now_utc()
    for model in (ProjectStoryboardShot, ProjectCopywriting):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.episode_no == episode_no, model.status != "needs_review")
            .values(status="needs_review", updated_at=current_time)
        )
    _mark_scripts_for_review(
        session,
        (ProjectEpisodeScript.project_id == project_id) & (ProjectEpisodeScript.episode_no == episode_no),
        current_time,
    )


def _mark_scripts_for_review(session, condition, current_time) -> None:
    """上游传播到结构化剧本时同步递增修订号，保证并发控制有效。"""
    session.execute(
        update(ProjectEpisodeScript)
        .where(condition, ProjectEpisodeScript.status != "needs_review")
        .values(
            status="needs_review",
            revision=ProjectEpisodeScript.revision + 1,
            updated_at=current_time,
        )
    )


def mark_script_downstream_for_review(session, project_id: str, episode_no: int) -> None:
    """剧本变化后，标记分镜和发布文案需要复核。"""
    current_time = now_utc()
    for model in (ProjectStoryboardShot, ProjectCopywriting):
        session.execute(
            update(model)
            .where(model.project_id == project_id, model.episode_no == episode_no, model.status != "needs_review")
            .values(status="needs_review", updated_at=current_time)
        )
