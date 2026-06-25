"""场次化分镜聚合、镜头编辑、排序和兼容接口。"""
from __future__ import annotations

import json
import time
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update

from app.core.db import get_session
from app.models.db_models import (
    Project,
    ProjectCharacterSnapshot,
    ProjectCopywriting,
    ProjectEpisodeScript,
    ProjectScriptBlock,
    ProjectScriptScene,
    ProjectShotPrompt,
    ProjectStoryboard,
    ProjectStoryboardShot,
)
from app.models.schemas import (
    ProjectStoryboardShotPayload,
    StoryboardDuplicatePayload,
    StoryboardReassignPayload,
    StoryboardReorderPayload,
)
from app.services.project.common import now_utc, validate_episode_no
from app.services.project.generation_common import call_text_generation_api
from app.services.user_skills import ensure_user_skill_enabled


CORE_FIELDS = (
    "source_scene_id", "shot_size", "subject_description", "visual_description", "action",
    "duration_seconds", "camera_angle", "camera_movement", "composition",
    "character_snapshot_ids", "expression", "environment", "props", "source_block_ids",
    "dialogue_snapshot", "voiceover_snapshot", "sound_effect", "music_note", "continuity_note",
)


class StoryboardConflictError(ValueError):
    """镜头修订号或排序集合冲突。"""


def _loads(value: str | None, fallback):
    try:
        return json.loads(value) if value else fallback
    except (json.JSONDecodeError, TypeError):
        return fallback


def _script_for_episode(session, project_id: str, episode_no: int) -> ProjectEpisodeScript | None:
    return session.scalars(select(ProjectEpisodeScript).where(
        ProjectEpisodeScript.project_id == project_id,
        ProjectEpisodeScript.episode_no == episode_no,
    )).first()


def _storyboard_for_episode(session, project_id: str, episode_no: int) -> ProjectStoryboard | None:
    return session.scalars(select(ProjectStoryboard).where(
        ProjectStoryboard.project_id == project_id,
        ProjectStoryboard.episode_no == episode_no,
    )).first()


def _ensure_storyboard(session, project: Project, episode_no: int) -> ProjectStoryboard:
    storyboard = _storyboard_for_episode(session, project.id, episode_no)
    if storyboard:
        return storyboard
    script = _script_for_episode(session, project.id, episode_no)
    now = now_utc()
    storyboard = ProjectStoryboard(
        id=str(uuid4()), project_id=project.id, episode_no=episode_no,
        version=0, revision=0, source_script_id=script.id if script else None,
        source_script_version=script.version if script else None,
        source_script_status=script.status if script else None,
        total_duration_seconds=0, status="draft", created_at=now, updated_at=now,
    )
    session.add(storyboard)
    session.flush()
    return storyboard


def _scenes(session, script_id: str | None) -> list[ProjectScriptScene]:
    if not script_id:
        return []
    return list(session.scalars(select(ProjectScriptScene).where(
        ProjectScriptScene.script_id == script_id
    ).order_by(ProjectScriptScene.sort_order)).all())


def _shots(session, storyboard_id: str) -> list[ProjectStoryboardShot]:
    return list(session.scalars(select(ProjectStoryboardShot).where(
        ProjectStoryboardShot.storyboard_id == storyboard_id
    ).order_by(ProjectStoryboardShot.source_scene_id, ProjectStoryboardShot.sort_order, ProjectStoryboardShot.created_at)).all())


def _prompt(session, shot_id: str) -> ProjectShotPrompt | None:
    return session.scalars(select(ProjectShotPrompt).where(ProjectShotPrompt.shot_id == shot_id)).first()


def _display_map(scenes: list[ProjectScriptScene], shots: list[ProjectStoryboardShot]) -> dict[str, str]:
    scene_numbers = {scene.id: index + 1 for index, scene in enumerate(scenes)}
    result: dict[str, str] = {}
    unassigned = 0
    for shot in sorted(shots, key=lambda item: (scene_numbers.get(item.source_scene_id or "", 10**6), item.sort_order, item.created_at)):
        if shot.source_scene_id in scene_numbers:
            result[shot.id] = f"S{scene_numbers[shot.source_scene_id]:02d}-{shot.sort_order + 1:03d}"
        else:
            unassigned += 1
            result[shot.id] = f"U-{unassigned:03d}"
    return result


def _serialize_prompt(prompt: ProjectShotPrompt | None) -> dict[str, Any]:
    if not prompt:
        return {
            "image_prompt": None, "video_prompt": None, "negative_prompt": None,
            "first_frame_description": None, "last_frame_description": None,
            "reference_asset_ids": [], "aspect_ratio": None, "seedance_prompt": None,
        }
    return {
        "image_prompt": prompt.image_prompt, "video_prompt": prompt.video_prompt,
        "negative_prompt": prompt.negative_prompt,
        "first_frame_description": prompt.first_frame_description,
        "last_frame_description": prompt.last_frame_description,
        "reference_asset_ids": _loads(prompt.reference_asset_ids, []),
        "aspect_ratio": prompt.aspect_ratio, "seedance_prompt": prompt.seedance_prompt,
    }


def _serialize_shot(shot: ProjectStoryboardShot, prompt: ProjectShotPrompt | None, display_code: str) -> dict[str, Any]:
    return {
        "id": shot.id, "project_id": shot.project_id, "episode_no": shot.episode_no,
        "storyboard_id": shot.storyboard_id, "source_scene_id": shot.source_scene_id,
        "display_code": display_code, "sort_order": shot.sort_order, "revision": shot.revision,
        "shot_size": shot.shot_size, "subject_description": shot.subject_description,
        "visual_description": shot.visual_description, "action": shot.action,
        "duration_seconds": shot.duration_seconds, "camera_angle": shot.camera_angle,
        "camera_movement": shot.camera_movement, "composition": shot.composition,
        "character_snapshot_ids": _loads(shot.character_snapshot_ids, []),
        "expression": shot.expression, "environment": shot.environment,
        "props": _loads(shot.props, []), "source_block_ids": _loads(shot.source_block_ids, []),
        "dialogue_snapshot": shot.dialogue_snapshot, "voiceover_snapshot": shot.voiceover_snapshot,
        "sound_effect": shot.sound_effect, "music_note": shot.music_note,
        "continuity_note": shot.continuity_note, "source_status": shot.source_status,
        "status": shot.status, "prompt": _serialize_prompt(prompt),
        "prompt_freshness": prompt.freshness if prompt else "current",
        "prompt_customized": prompt.customized if prompt else False,
        # 旧字段只作为响应兼容镜像。
        "shot_no": shot.shot_no, "scene": shot.scene, "visual_prompt": shot.visual_prompt,
        "camera": shot.camera, "dialogue_or_voiceover": shot.dialogue_or_voiceover,
        "created_at": shot.created_at.isoformat(), "updated_at": shot.updated_at.isoformat(),
    }


def _group_status(shots: list[ProjectStoryboardShot]) -> str:
    if any(shot.status == "needs_review" or shot.source_status in {"scene_deleted", "unassigned"} for shot in shots):
        return "needs_review"
    if shots and all(shot.status == "confirmed" for shot in shots):
        return "confirmed"
    if shots and all(shot.status in {"confirmed", "pending_review"} for shot in shots):
        return "pending_review"
    return "draft"


def _serialize_storyboard(session, storyboard: ProjectStoryboard) -> dict[str, Any]:
    scenes = _scenes(session, storyboard.source_script_id)
    shots = _shots(session, storyboard.id)
    prompts = {prompt.shot_id: prompt for prompt in session.scalars(select(ProjectShotPrompt).where(
        ProjectShotPrompt.shot_id.in_([shot.id for shot in shots] or ["-"])
    )).all()}
    display_codes = _display_map(scenes, shots)
    shots_by_scene: dict[str | None, list[ProjectStoryboardShot]] = {}
    for shot in shots:
        shots_by_scene.setdefault(shot.source_scene_id, []).append(shot)
    groups = []
    for scene_no, scene in enumerate(scenes, 1):
        group_shots = sorted(shots_by_scene.pop(scene.id, []), key=lambda item: item.sort_order)
        duration = round(sum(shot.duration_seconds or 0 for shot in group_shots), 1)
        effective = scene.effective_duration_seconds
        deviation = round((duration - effective) / effective * 100, 1) if effective else None
        groups.append({
            "scene_id": scene.id, "scene_no": scene_no, "display_code": f"S{scene_no:02d}",
            "title": scene.title or scene.location or f"场次 {scene_no}",
            "script_duration_seconds": effective, "shots_duration_seconds": duration,
            "duration_deviation_percent": deviation, "status": _group_status(group_shots),
            "shots": [_serialize_shot(shot, prompts.get(shot.id), display_codes[shot.id]) for shot in group_shots],
        })
    unassigned = [shot for remaining in shots_by_scene.values() for shot in remaining]
    if unassigned:
        unassigned.sort(key=lambda item: (item.sort_order, item.created_at))
        groups.append({
            "scene_id": None, "scene_no": None, "display_code": "U",
            "title": "未归属场次", "script_duration_seconds": None,
            "shots_duration_seconds": round(sum(shot.duration_seconds or 0 for shot in unassigned), 1),
            "duration_deviation_percent": None, "status": "needs_review",
            "shots": [_serialize_shot(shot, prompts.get(shot.id), display_codes[shot.id]) for shot in unassigned],
        })
    return {
        "id": storyboard.id, "project_id": storyboard.project_id, "episode_no": storyboard.episode_no,
        "version": storyboard.version, "revision": storyboard.revision,
        "source_script_id": storyboard.source_script_id,
        "source_script_version": storyboard.source_script_version,
        "source_script_status": storyboard.source_script_status,
        "total_duration_seconds": storyboard.total_duration_seconds,
        "status": storyboard.status, "shot_count": len(shots), "scene_groups": groups,
        "created_at": storyboard.created_at.isoformat(), "updated_at": storyboard.updated_at.isoformat(),
    }


def get_storyboard(project_id: str, episode_no: int) -> dict[str, Any] | None:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        storyboard = _storyboard_for_episode(session, project_id, episode_no)
        return _serialize_storyboard(session, storyboard) if storyboard else None


async def generate_storyboard_scene(project_id: str, episode_no: int, scene_id: str) -> dict[str, Any]:
    """按场次生成，避免整集长请求导致前端 fetch 中断。"""
    ensure_user_skill_enabled("short-drama-creator")

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        script = _script_for_episode(session, project_id, episode_no)
        scene = session.get(ProjectScriptScene, scene_id)
        if not script or not scene or scene.script_id != script.id:
            raise ValueError("来源场次不属于当前集剧本")
        blocks = list(session.scalars(select(ProjectScriptBlock).where(
            ProjectScriptBlock.scene_id == scene.id
        ).order_by(ProjectScriptBlock.sort_order)).all())
        allowed_characters = set(_loads(scene.character_snapshot_ids, []))
        snapshot = {
            "episode_no": episode_no,
            "scene": {
                "id": scene.id, "title": scene.title, "location": scene.location,
                "time_of_day": scene.time_of_day, "interior_exterior": scene.interior_exterior,
                "duration_seconds": scene.effective_duration_seconds,
                "character_snapshot_ids": list(allowed_characters),
                "blocks": [{"id": block.id, "type": block.block_type, "content": block.content,
                            "character_snapshot_id": block.character_snapshot_id} for block in blocks],
            },
        }
    prompt = (
        "将以下单个短剧场次拆为可拍摄镜头。只返回 JSON："
        "{shots:[{shot_size,subject_description,visual_description,action,duration_seconds,"
        "camera_angle,camera_movement,composition,character_snapshot_ids,expression,environment,props,"
        "source_block_ids,dialogue_snapshot,voiceover_snapshot,sound_effect,music_note,continuity_note,"
        "prompt:{image_prompt,video_prompt,negative_prompt,first_frame_description,last_frame_description,"
        "reference_asset_ids,aspect_ratio,seedance_prompt}}]}。"
        "只能使用上下文中给出的人物和内容块 ID；镜头数 1-30；时长必须大于 0。\n"
        f"上下文：{json.dumps(snapshot, ensure_ascii=False)}"
    )
    started = time.perf_counter()
    output = await call_text_generation_api("生成顺序明确、连续性可检查的中文短剧分镜。", prompt, max_tokens=6000)
    raw_shots = output.get("shots") if isinstance(output, dict) else None
    if not isinstance(raw_shots, list) or not 1 <= len(raw_shots) <= 30:
        raise ValueError("模型未返回有效镜头列表")
    allowed_blocks = {block["id"] for block in snapshot["scene"]["blocks"]}
    payloads = []
    for raw in raw_shots:
        if not isinstance(raw, dict):
            raise ValueError("模型返回的镜头格式无效")
        raw["source_scene_id"] = scene_id
        raw["status"] = "draft"
        raw["character_snapshot_ids"] = [item for item in raw.get("character_snapshot_ids", []) if item in allowed_characters]
        raw["source_block_ids"] = [item for item in raw.get("source_block_ids", []) if item in allowed_blocks]
        raw.setdefault("props", [])
        raw.setdefault("prompt", {}).setdefault("reference_asset_ids", [])
        payloads.append(ProjectStoryboardShotPayload.model_validate(raw))
    created = [create_storyboard_shot(project_id, episode_no, payload) for payload in payloads]
    return {
        "scene_id": scene_id, "status": "succeeded", "shot_count": len(created),
        "shot_ids": [shot["id"] for shot in created],
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
    }


def _validate_references(session, project_id: str, script_id: str | None, payload: ProjectStoryboardShotPayload) -> None:
    if payload.source_scene_id:
        scene = session.get(ProjectScriptScene, payload.source_scene_id)
        if not scene or scene.script_id != script_id:
            raise ValueError("来源场次不属于当前集剧本")
    character_ids = set(session.scalars(select(ProjectCharacterSnapshot.id).where(
        ProjectCharacterSnapshot.project_id == project_id
    )).all())
    if any(item not in character_ids for item in payload.character_snapshot_ids):
        raise ValueError("镜头引用的角色不属于当前项目")
    if payload.source_block_ids:
        blocks = session.scalars(select(ProjectScriptBlock).where(
            ProjectScriptBlock.id.in_(payload.source_block_ids)
        )).all()
        if len(blocks) != len(set(payload.source_block_ids)) or any(block.scene_id != payload.source_scene_id for block in blocks):
            raise ValueError("来源内容块不属于当前场次")


def _next_order(session, storyboard_id: str, scene_id: str | None) -> int:
    shots = session.scalars(select(ProjectStoryboardShot.sort_order).where(
        ProjectStoryboardShot.storyboard_id == storyboard_id,
        ProjectStoryboardShot.source_scene_id == scene_id,
    )).all()
    return max(shots, default=-1) + 1


def _apply_payload(session, shot: ProjectStoryboardShot, payload: ProjectStoryboardShotPayload, *, creating: bool) -> ProjectShotPrompt:
    if not creating and payload.revision is not None and payload.revision != shot.revision:
        raise StoryboardConflictError("镜头已在其他操作中更新，请刷新后合并")
    before = {field: getattr(shot, field) for field in CORE_FIELDS if hasattr(shot, field)}
    supplied = payload.model_fields_set
    for field in (
        "source_scene_id", "shot_size", "subject_description", "visual_description", "action",
        "duration_seconds", "camera_angle", "camera_movement", "composition", "expression",
        "environment", "dialogue_snapshot", "voiceover_snapshot", "sound_effect", "music_note",
        "continuity_note", "status",
    ):
        if creating or field in supplied:
            setattr(shot, field, getattr(payload, field))
    if creating or "character_snapshot_ids" in supplied:
        shot.character_snapshot_ids = json.dumps(payload.character_snapshot_ids, ensure_ascii=False)
    if creating or "props" in supplied:
        shot.props = json.dumps(payload.props, ensure_ascii=False)
    if creating or "source_block_ids" in supplied:
        shot.source_block_ids = json.dumps(payload.source_block_ids, ensure_ascii=False)
    shot.source_status = "valid" if shot.source_scene_id else "unassigned"
    # 旧字段镜像确保兼容接口仍能读取。
    if creating or "scene" in supplied or "subject_description" in supplied:
        shot.scene = payload.scene or payload.subject_description
    if creating or "visual_prompt" in supplied or "prompt" in supplied:
        shot.visual_prompt = payload.visual_prompt or payload.prompt.image_prompt
    if creating or "camera" in supplied or "camera_angle" in supplied:
        shot.camera = payload.camera or payload.camera_angle
    if creating or {"dialogue_or_voiceover", "dialogue_snapshot", "voiceover_snapshot"} & supplied:
        shot.dialogue_or_voiceover = payload.dialogue_or_voiceover or payload.dialogue_snapshot or payload.voiceover_snapshot
    shot.revision = 1 if creating else shot.revision + 1
    shot.updated_at = now_utc()
    prompt = _prompt(session, shot.id)
    if not prompt:
        prompt = ProjectShotPrompt(id=str(uuid4()), shot_id=shot.id, source_shot_revision=shot.revision, updated_at=shot.updated_at)
        session.add(prompt)
    prompt_payload = payload.prompt.model_copy()
    if payload.visual_prompt and "prompt" not in supplied:
        prompt_payload.image_prompt = payload.visual_prompt
    should_update_prompt = creating or "prompt" in supplied or "visual_prompt" in supplied
    prompt_changed = any(getattr(prompt, field) != getattr(prompt_payload, field) for field in (
        "image_prompt", "video_prompt", "negative_prompt", "first_frame_description",
        "last_frame_description", "aspect_ratio", "seedance_prompt",
    )) or _loads(prompt.reference_asset_ids, []) != prompt_payload.reference_asset_ids
    if should_update_prompt:
        for field in (
            "image_prompt", "video_prompt", "negative_prompt", "first_frame_description",
            "last_frame_description", "aspect_ratio", "seedance_prompt",
        ):
            setattr(prompt, field, getattr(prompt_payload, field))
        prompt.reference_asset_ids = json.dumps(prompt_payload.reference_asset_ids, ensure_ascii=False)
    if should_update_prompt and prompt_changed:
        prompt.customized = True
        prompt.source_shot_revision = shot.revision
        prompt.freshness = "current"
    elif not creating:
        after = {field: getattr(shot, field) for field in CORE_FIELDS if hasattr(shot, field)}
        if before != after and prompt.customized:
            prompt.freshness = "needs_update"
    prompt.updated_at = shot.updated_at
    return prompt


def _touch_storyboard(session, project: Project, storyboard: ProjectStoryboard) -> None:
    storyboard.version += 1
    storyboard.revision += 1
    storyboard.status = "draft"
    storyboard.updated_at = now_utc()
    shots = _shots(session, storyboard.id)
    storyboard.total_duration_seconds = round(sum(shot.duration_seconds or 0 for shot in shots), 1)
    project.updated_at = storyboard.updated_at
    session.execute(update(ProjectCopywriting).where(
        ProjectCopywriting.project_id == project.id,
        ProjectCopywriting.episode_no == storyboard.episode_no,
        ProjectCopywriting.status != "needs_review",
    ).values(status="needs_review", updated_at=storyboard.updated_at))


def create_storyboard_shot(project_id: str, episode_no: int, payload: ProjectStoryboardShotPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        storyboard = _ensure_storyboard(session, project, episode_no)
        _validate_references(session, project_id, storyboard.source_script_id, payload)
        now = now_utc()
        shot = ProjectStoryboardShot(
            id=str(uuid4()), project_id=project_id, episode_no=episode_no, storyboard_id=storyboard.id,
            source_scene_id=payload.source_scene_id,
            sort_order=_next_order(session, storyboard.id, payload.source_scene_id),
            revision=1, shot_no=1, source_status="valid" if payload.source_scene_id else "unassigned",
            status="draft", created_at=now, updated_at=now,
        )
        session.add(shot)
        session.flush()
        _apply_payload(session, shot, payload, creating=True)
        session.flush()
        _renumber(session, storyboard)
        _touch_storyboard(session, project, storyboard)
        session.flush()
        data = _serialize_storyboard(session, storyboard)
        return next(item for group in data["scene_groups"] for item in group["shots"] if item["id"] == shot.id)


def update_storyboard_shot(project_id: str, episode_no: int, shot_id: str, payload: ProjectStoryboardShotPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        shot = session.get(ProjectStoryboardShot, shot_id)
        if not shot or shot.project_id != project_id or shot.episode_no != episode_no or not shot.storyboard_id:
            raise ValueError("项目分镜不存在")
        storyboard = session.get(ProjectStoryboard, shot.storyboard_id)
        _validate_references(session, project_id, storyboard.source_script_id, payload)
        old_scene_id = shot.source_scene_id
        _apply_payload(session, shot, payload, creating=False)
        if old_scene_id != shot.source_scene_id:
            shot.sort_order = _next_order(session, storyboard.id, shot.source_scene_id)
            _normalize_scene_order(session, storyboard.id, old_scene_id)
        session.flush()
        _renumber(session, storyboard)
        _touch_storyboard(session, project, storyboard)
        session.flush()
        data = _serialize_storyboard(session, storyboard)
        return next(item for group in data["scene_groups"] for item in group["shots"] if item["id"] == shot.id)


def delete_storyboard_shot(project_id: str, episode_no: int, shot_id: str) -> dict[str, bool]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        shot = session.get(ProjectStoryboardShot, shot_id)
        if not shot or shot.project_id != project_id or shot.episode_no != episode_no or not shot.storyboard_id:
            raise ValueError("项目分镜不存在")
        storyboard = session.get(ProjectStoryboard, shot.storyboard_id)
        scene_id = shot.source_scene_id
        prompt = _prompt(session, shot.id)
        if prompt:
            session.delete(prompt)
        session.delete(shot)
        session.flush()
        _normalize_scene_order(session, storyboard.id, scene_id)
        _renumber(session, storyboard)
        _touch_storyboard(session, project, storyboard)
        return {"ok": True}


def reorder_storyboard_scene(project_id: str, episode_no: int, scene_id: str, payload: StoryboardReorderPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        storyboard = _storyboard_for_episode(session, project_id, episode_no)
        if not storyboard:
            raise ValueError("项目分镜不存在")
        shots = list(session.scalars(select(ProjectStoryboardShot).where(
            ProjectStoryboardShot.storyboard_id == storyboard.id,
            ProjectStoryboardShot.source_scene_id == scene_id,
        )).all())
        if set(payload.shot_ids) != {shot.id for shot in shots} or len(payload.shot_ids) != len(shots):
            raise StoryboardConflictError("镜头排序集合已变化，请刷新后重试")
        by_id = {shot.id: shot for shot in shots}
        for index, shot_id in enumerate(payload.shot_ids):
            by_id[shot_id].sort_order = index
            by_id[shot_id].updated_at = now_utc()
        _renumber(session, storyboard)
        _touch_storyboard(session, project, storyboard)
        session.flush()
        return _serialize_storyboard(session, storyboard)


def reassign_storyboard_shot(project_id: str, episode_no: int, shot_id: str, payload: StoryboardReassignPayload) -> dict[str, Any]:
    with get_session() as session:
        shot = session.get(ProjectStoryboardShot, shot_id)
        storyboard = _storyboard_for_episode(session, project_id, episode_no)
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        if not shot or not storyboard or shot.storyboard_id != storyboard.id:
            raise ValueError("项目分镜不存在")
        scene = session.get(ProjectScriptScene, payload.source_scene_id)
        if not scene or scene.script_id != storyboard.source_script_id:
            raise ValueError("来源场次不属于当前集剧本")
        old_scene_id = shot.source_scene_id
        shot.source_scene_id = scene.id
        shot.sort_order = _next_order(session, storyboard.id, scene.id)
        shot.source_status = "valid"
        shot.revision += 1
        shot.status = "draft"
        shot.updated_at = now_utc()
        _normalize_scene_order(session, storyboard.id, old_scene_id)
        _renumber(session, storyboard)
        _touch_storyboard(session, project, storyboard)
        session.flush()
        data = _serialize_storyboard(session, storyboard)
        return next(item for group in data["scene_groups"] for item in group["shots"] if item["id"] == shot.id)


def duplicate_storyboard_shot(project_id: str, episode_no: int, shot_id: str, payload: StoryboardDuplicatePayload) -> dict[str, Any]:
    with get_session() as session:
        original = session.get(ProjectStoryboardShot, shot_id)
        storyboard = _storyboard_for_episode(session, project_id, episode_no)
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        if not original or not storyboard or original.storyboard_id != storyboard.id:
            raise ValueError("项目分镜不存在")
        target_scene_id = payload.target_scene_id or original.source_scene_id
        if target_scene_id:
            target_scene = session.get(ProjectScriptScene, target_scene_id)
            if not target_scene or target_scene.script_id != storyboard.source_script_id:
                raise ValueError("来源场次不属于当前集剧本")
        now = now_utc()
        clone = ProjectStoryboardShot(
            id=str(uuid4()), project_id=project_id, episode_no=episode_no, storyboard_id=storyboard.id,
            source_scene_id=target_scene_id, sort_order=_next_order(session, storyboard.id, target_scene_id),
            revision=1, shot_no=1, shot_size=original.shot_size,
            subject_description=original.subject_description, visual_description=original.visual_description,
            action=original.action, camera_angle=original.camera_angle, camera_movement=original.camera_movement,
            composition=original.composition, character_snapshot_ids=original.character_snapshot_ids,
            expression=original.expression, environment=original.environment, props=original.props,
            source_block_ids=original.source_block_ids, dialogue_snapshot=original.dialogue_snapshot,
            voiceover_snapshot=original.voiceover_snapshot, sound_effect=original.sound_effect,
            music_note=original.music_note, continuity_note=original.continuity_note,
            duration_seconds=original.duration_seconds, source_status="valid" if target_scene_id else "unassigned",
            scene=original.scene, visual_prompt=original.visual_prompt, camera=original.camera,
            dialogue_or_voiceover=original.dialogue_or_voiceover, status="draft",
            created_at=now, updated_at=now,
        )
        session.add(clone)
        session.flush()
        original_prompt = _prompt(session, original.id)
        if original_prompt:
            session.add(ProjectShotPrompt(
                id=str(uuid4()), shot_id=clone.id, source_shot_revision=1,
                image_prompt=original_prompt.image_prompt, video_prompt=original_prompt.video_prompt,
                negative_prompt=original_prompt.negative_prompt,
                first_frame_description=original_prompt.first_frame_description,
                last_frame_description=original_prompt.last_frame_description,
                reference_asset_ids=original_prompt.reference_asset_ids,
                aspect_ratio=original_prompt.aspect_ratio, seedance_prompt=original_prompt.seedance_prompt,
                customized=original_prompt.customized, freshness=original_prompt.freshness, updated_at=now,
            ))
        _renumber(session, storyboard)
        _touch_storyboard(session, project, storyboard)
        session.flush()
        data = _serialize_storyboard(session, storyboard)
        return next(item for group in data["scene_groups"] for item in group["shots"] if item["id"] == clone.id)


def _normalize_scene_order(session, storyboard_id: str, scene_id: str | None) -> None:
    shots = session.scalars(select(ProjectStoryboardShot).where(
        ProjectStoryboardShot.storyboard_id == storyboard_id,
        ProjectStoryboardShot.source_scene_id == scene_id,
    ).order_by(ProjectStoryboardShot.sort_order, ProjectStoryboardShot.created_at)).all()
    for index, shot in enumerate(shots):
        shot.sort_order = index


def _renumber(session, storyboard: ProjectStoryboard) -> None:
    scenes = _scenes(session, storyboard.source_script_id)
    scene_numbers = {scene.id: index for index, scene in enumerate(scenes)}
    shots = _shots(session, storyboard.id)
    ordered = sorted(shots, key=lambda item: (scene_numbers.get(item.source_scene_id or "", 10**6), item.sort_order, item.created_at))
    for number, shot in enumerate(ordered, 1):
        shot.shot_no = number


# 兼容旧接口：使用聚合服务，但保留原路径和列表形状。
def list_storyboard_shots(project_id: str, episode_no: int) -> list[dict[str, Any]]:
    storyboard = get_storyboard(project_id, episode_no)
    return [shot for group in storyboard["scene_groups"] for shot in group["shots"]] if storyboard else []
