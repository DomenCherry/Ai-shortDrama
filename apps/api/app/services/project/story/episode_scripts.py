"""结构化剧本聚合、候选版本、检查和确认服务。"""
from __future__ import annotations

import json
import time
from typing import Any
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import delete, select

from app.core.db import get_session
from app.models.db_models import (
    Project,
    ProjectCharacterSnapshot,
    ProjectEpisodeContent,
    ProjectEpisodeOutline,
    ProjectEpisodeScript,
    ProjectEpisodeScriptVersion,
    ProjectScriptBlock,
    ProjectScriptCheckRun,
    ProjectScriptGeneration,
    ProjectScriptScene,
    ProjectStoryOutline,
    ProjectWorldSnapshot,
)
from app.models.schemas import (
    ProjectEpisodeScriptPayload,
    ScriptBlockPayload,
    ScriptCheckPayload,
    ScriptGenerationCreate,
    ScriptRevisionPayload,
    ScriptScenePayload,
)
from app.services import model_configs
from app.services.project.common import (
    character_snapshot_to_response,
    episode_content_to_response,
    episode_outline_to_response,
    mark_script_downstream_for_review,
    now_utc,
    project_to_response,
    story_outline_to_response,
    validate_episode_no,
    world_snapshot_to_response,
)
from app.services.project.generation_common import call_text_generation_api


BLOCK_TYPES = {"action", "dialogue", "voiceover", "transition"}
PRESET_LABELS = {
    "more_satisfying": "更爽",
    "more_tragic": "更虐",
    "more_suspenseful": "更悬疑",
    "more_colloquial": "更口语化",
    "short_video_pacing": "更短视频化",
    "compress_duration": "压缩时长",
    "stronger_cliffhanger": "增强结尾悬念",
}


class ScriptConflictError(ValueError):
    """剧本修订或候选基准冲突。"""


class ScriptValidationError(ValueError):
    """结构合同或确认门槛失败。"""

    def __init__(self, message: str, issues: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.issues = issues or []


def _loads(value: str | None, fallback):
    if not value:
        return fallback
    try:
        result = json.loads(value)
        return result
    except (json.JSONDecodeError, TypeError):
        return fallback


def _visible_count(value: str | None) -> int:
    return sum(1 for char in value or "" if not char.isspace())


def _block_duration(block_type: str, content: str | None) -> float:
    count = _visible_count(content)
    if block_type == "dialogue":
        return max(1.0, count / 4.0)
    if block_type == "voiceover":
        return max(1.0, count / 3.5)
    if block_type == "transition":
        return max(2.0, count / 8.0)
    return max(1.0, count / 8.0)


def _source_content_version(content: ProjectEpisodeContent | None) -> str | None:
    if not content:
        return None
    return f"{content.id}:{content.updated_at.isoformat()}"


def _script_for_episode(session, project_id: str, episode_no: int) -> ProjectEpisodeScript | None:
    return session.scalars(
        select(ProjectEpisodeScript).where(
            ProjectEpisodeScript.project_id == project_id,
            ProjectEpisodeScript.episode_no == episode_no,
        )
    ).first()


def _scene_rows(session, script_id: str) -> list[ProjectScriptScene]:
    return list(session.scalars(
        select(ProjectScriptScene).where(ProjectScriptScene.script_id == script_id).order_by(ProjectScriptScene.sort_order)
    ).all())


def _block_rows(session, scene_id: str) -> list[ProjectScriptBlock]:
    return list(session.scalars(
        select(ProjectScriptBlock).where(ProjectScriptBlock.scene_id == scene_id).order_by(ProjectScriptBlock.sort_order)
    ).all())


def _structure_issues_from_rows(scenes: list[dict[str, Any]], target_seconds: float, effective_seconds: float) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not scenes:
        issues.append({"code": "script_empty", "severity": "error", "message": "剧本至少需要一个场次", "scene_id": None, "block_id": None, "details": {}})
    for number, scene in enumerate(scenes, 1):
        scene_id = scene.get("id")
        for field, label in (("location", "地点"), ("time_of_day", "时间"), ("interior_exterior", "内外景")):
            if not scene.get(field):
                issues.append({"code": f"scene_{field}_required", "severity": "error", "message": f"第 {number} 场缺少{label}", "scene_id": scene_id, "block_id": None, "details": {"scene_no": number, "field": field}})
        blocks = scene.get("blocks", [])
        non_empty = [block for block in blocks if (block.get("content") or "").strip()]
        if not non_empty:
            issues.append({"code": "scene_blocks_required", "severity": "error", "message": f"第 {number} 场至少需要一个非空内容块", "scene_id": scene_id, "block_id": None, "details": {"scene_no": number}})
        for block in blocks:
            block_id = block.get("id")
            if block.get("block_type") not in BLOCK_TYPES:
                issues.append({"code": "block_type_invalid", "severity": "error", "message": f"第 {number} 场存在无效内容块类型", "scene_id": scene_id, "block_id": block_id, "details": {}})
            if not (block.get("content") or "").strip():
                issues.append({"code": "block_content_required", "severity": "error", "message": f"第 {number} 场存在空内容块", "scene_id": scene_id, "block_id": block_id, "details": {}})
            if block.get("block_type") == "dialogue" and not block.get("character_snapshot_id") and not (block.get("temporary_speaker_name") or "").strip():
                issues.append({"code": "dialogue_speaker_required", "severity": "error", "message": f"第 {number} 场的对白缺少说话人", "scene_id": scene_id, "block_id": block_id, "details": {}})
    if target_seconds > 0:
        deviation = abs(effective_seconds - target_seconds) / target_seconds * 100
        if deviation > 10:
            code = "duration_severe_deviation" if deviation > 25 else "duration_deviation"
            issues.append({"code": code, "severity": "warning", "message": f"剧本时长与项目目标偏差 {deviation:.1f}%", "scene_id": None, "block_id": None, "details": {"deviation_percent": round(deviation, 1)}})
    return issues


def _serialize_script(session, project: Project, script: ProjectEpisodeScript) -> dict[str, Any]:
    character_rows = session.scalars(
        select(ProjectCharacterSnapshot).where(ProjectCharacterSnapshot.project_id == project.id)
    ).all()
    characters = {item.id: item for item in character_rows}
    scenes: list[dict[str, Any]] = []
    for scene_no, scene in enumerate(_scene_rows(session, script.id), 1):
        blocks = [
            {
                "id": block.id,
                "scene_id": block.scene_id,
                "block_type": block.block_type,
                "character_snapshot_id": block.character_snapshot_id,
                "temporary_speaker_name": block.temporary_speaker_name,
                "content": block.content,
                "emotion": block.emotion,
                "performance_note": block.performance_note,
                "sort_order": block.sort_order,
                "created_at": block.created_at.isoformat(),
                "updated_at": block.updated_at.isoformat(),
            }
            for block in _block_rows(session, scene.id)
        ]
        character_ids = _loads(scene.character_snapshot_ids, [])
        refs = [
            {"character_snapshot_id": character.id, "name": character.name, "updated_at": character.updated_at.isoformat()}
            for character_id in character_ids
            if (character := characters.get(character_id))
        ]
        scenes.append({
            "id": scene.id,
            "script_id": scene.script_id,
            "scene_no": scene_no,
            "title": scene.title,
            "location": scene.location,
            "time_of_day": scene.time_of_day,
            "interior_exterior": scene.interior_exterior,
            "character_snapshot_ids": character_ids,
            "character_refs": refs,
            "auto_duration_seconds": scene.auto_duration_seconds,
            "manual_duration_seconds": scene.manual_duration_seconds,
            "effective_duration_seconds": scene.effective_duration_seconds,
            "story_purpose": scene.story_purpose,
            "sort_order": scene.sort_order,
            "blocks": blocks,
            "created_at": scene.created_at.isoformat(),
            "updated_at": scene.updated_at.isoformat(),
        })
    target = round((project.episode_duration or 0) * 60, 1)
    deviation = round(script.effective_duration_seconds - target, 1)
    deviation_percent = round(deviation / target * 100, 1) if target else 0
    issues = _structure_issues_from_rows(scenes, target, script.effective_duration_seconds)
    return {
        "id": script.id,
        "project_id": script.project_id,
        "episode_no": script.episode_no,
        "title": script.title,
        "revision": script.revision,
        "version": script.version,
        "source_content_version": script.source_content_version,
        "auto_duration_seconds": script.auto_duration_seconds,
        "manual_duration_seconds": script.manual_duration_seconds,
        "effective_duration_seconds": script.effective_duration_seconds,
        "target_duration_seconds": target,
        "duration_deviation_seconds": deviation,
        "duration_deviation_percent": deviation_percent,
        "status": script.status,
        "confirmed_at": script.confirmed_at.isoformat() if script.confirmed_at else None,
        "scenes": scenes,
        "validation_issues": issues,
        "created_at": script.created_at.isoformat(),
        "updated_at": script.updated_at.isoformat(),
    }


def _substantive_signature(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "manual_duration_seconds": data.get("manual_duration_seconds"),
        "scenes": [
            {
                "id": scene.get("id"),
                "location": scene.get("location"),
                "time_of_day": scene.get("time_of_day"),
                "interior_exterior": scene.get("interior_exterior"),
                "character_snapshot_ids": scene.get("character_snapshot_ids", []),
                "manual_duration_seconds": scene.get("manual_duration_seconds"),
                "story_purpose": scene.get("story_purpose"),
                "blocks": [
                    {key: block.get(key) for key in ("id", "block_type", "character_snapshot_id", "temporary_speaker_name", "content", "emotion", "performance_note")}
                    for block in scene.get("blocks", [])
                ],
            }
            for scene in data.get("scenes", [])
        ],
    }


def _payload_dict(payload: ProjectEpisodeScriptPayload) -> dict[str, Any]:
    return payload.model_dump(mode="json")


def _validate_payload_ownership(session, project_id: str, script: ProjectEpisodeScript | None, payload: ProjectEpisodeScriptPayload) -> None:
    valid_characters = set(session.scalars(
        select(ProjectCharacterSnapshot.id).where(ProjectCharacterSnapshot.project_id == project_id)
    ).all())
    existing_scenes = {scene.id for scene in _scene_rows(session, script.id)} if script else set()
    existing_blocks = set()
    if script:
        for scene_id in existing_scenes:
            existing_blocks.update(block.id for block in _block_rows(session, scene_id))
    supplied_scene_ids: set[str] = set()
    supplied_block_ids: set[str] = set()
    for scene in payload.scenes:
        if scene.id:
            if scene.id not in existing_scenes or scene.id in supplied_scene_ids:
                raise ScriptValidationError("场次 ID 不属于当前剧本或重复")
            supplied_scene_ids.add(scene.id)
        if len(scene.character_snapshot_ids) != len(set(scene.character_snapshot_ids)):
            raise ScriptValidationError("场次人物引用不能重复")
        if any(character_id not in valid_characters for character_id in scene.character_snapshot_ids):
            raise ScriptValidationError("场次引用的角色不属于当前项目")
        for block in scene.blocks:
            if block.id:
                if block.id not in existing_blocks or block.id in supplied_block_ids:
                    raise ScriptValidationError("内容块 ID 不属于当前剧本或重复")
                supplied_block_ids.add(block.id)
            if block.character_snapshot_id and block.character_snapshot_id not in valid_characters:
                raise ScriptValidationError("对白引用的角色不属于当前项目")


def _write_version(session, script: ProjectEpisodeScript, response: dict[str, Any], change_source: str, generation_id: str | None = None) -> None:
    session.add(ProjectEpisodeScriptVersion(
        id=str(uuid4()), script_id=script.id, version=script.version,
        source_content_version=script.source_content_version,
        snapshot=json.dumps(response, ensure_ascii=False), change_source=change_source,
        generation_id=generation_id, created_at=now_utc(),
    ))


def _save_in_session(
    session,
    project: Project,
    episode_no: int,
    payload: ProjectEpisodeScriptPayload,
    *,
    change_source: str = "manual_save",
    generation_id: str | None = None,
) -> dict[str, Any]:
    script = _script_for_episode(session, project.id, episode_no)
    if script and payload.revision != script.revision:
        raise ScriptConflictError("剧本已在其他操作中更新")
    if not script and payload.revision is not None:
        raise ScriptConflictError("剧本尚不存在，请刷新后重试")
    _validate_payload_ownership(session, project.id, script, payload)

    current_response = _serialize_script(session, project, script) if script else {"scenes": [], "manual_duration_seconds": None}
    requested = _payload_dict(payload)
    substantive = not script or _substantive_signature(current_response) != _substantive_signature(requested)
    now = now_utc()
    content = session.scalars(select(ProjectEpisodeContent).where(
        ProjectEpisodeContent.project_id == project.id, ProjectEpisodeContent.episode_no == episode_no
    )).first()
    if not script:
        script = ProjectEpisodeScript(
            id=str(uuid4()), project_id=project.id, episode_no=episode_no,
            title=payload.title, revision=1, version=1,
            source_content_version=_source_content_version(content), auto_duration_seconds=0,
            manual_duration_seconds=payload.manual_duration_seconds, effective_duration_seconds=0,
            status="draft", created_at=now, updated_at=now,
        )
        session.add(script)
        session.flush()
    else:
        script.revision += 1
        if substantive:
            script.version += 1
            script.status = "draft"
        script.title = payload.title
        script.manual_duration_seconds = payload.manual_duration_seconds
        script.source_content_version = _source_content_version(content)
        script.updated_at = now

    existing_scenes = {item.id: item for item in _scene_rows(session, script.id)}
    existing_blocks: dict[str, ProjectScriptBlock] = {}
    for scene in existing_scenes.values():
        existing_blocks.update({item.id: item for item in _block_rows(session, scene.id)})
    session.execute(delete(ProjectScriptBlock).where(ProjectScriptBlock.scene_id.in_(list(existing_scenes) or ["-"])))
    session.execute(delete(ProjectScriptScene).where(ProjectScriptScene.script_id == script.id))
    session.flush()

    total_auto = 0.0
    total_scene_effective = 0.0
    pending_blocks: list[tuple[str, list[ScriptBlockPayload]]] = []
    for scene_order, scene_payload in enumerate(payload.scenes):
        scene_id = scene_payload.id or str(uuid4())
        scene_created = existing_scenes.get(scene_id).created_at if scene_id in existing_scenes else now
        auto_duration = round(sum(_block_duration(block.block_type, block.content) for block in scene_payload.blocks), 1)
        effective_duration = scene_payload.manual_duration_seconds if scene_payload.manual_duration_seconds is not None else auto_duration
        total_auto += auto_duration
        total_scene_effective += effective_duration
        session.add(ProjectScriptScene(
            id=scene_id, script_id=script.id, title=scene_payload.title, location=scene_payload.location,
            time_of_day=scene_payload.time_of_day, interior_exterior=scene_payload.interior_exterior,
            character_snapshot_ids=json.dumps(scene_payload.character_snapshot_ids, ensure_ascii=False),
            auto_duration_seconds=auto_duration, manual_duration_seconds=scene_payload.manual_duration_seconds,
            effective_duration_seconds=effective_duration, story_purpose=scene_payload.story_purpose,
            sort_order=scene_order, created_at=scene_created, updated_at=now,
        ))
        pending_blocks.append((scene_id, scene_payload.blocks))

    # 场次与内容块没有 ORM relationship，SQLAlchemy 无法仅根据对象引用推导
    # 插入顺序。先显式写入全部父场次，避免 PostgreSQL 外键拒绝内容块。
    session.flush()
    for scene_id, block_payloads in pending_blocks:
        for block_order, block_payload in enumerate(block_payloads):
            block_id = block_payload.id or str(uuid4())
            block_created = existing_blocks.get(block_id).created_at if block_id in existing_blocks else now
            session.add(ProjectScriptBlock(
                id=block_id, scene_id=scene_id, block_type=block_payload.block_type,
                character_snapshot_id=block_payload.character_snapshot_id,
                temporary_speaker_name=block_payload.temporary_speaker_name if block_payload.block_type == "dialogue" else None,
                content=block_payload.content, emotion=block_payload.emotion,
                performance_note=block_payload.performance_note, sort_order=block_order,
                created_at=block_created, updated_at=now,
            ))
    script.auto_duration_seconds = round(total_auto, 1)
    script.effective_duration_seconds = round(
        script.manual_duration_seconds if script.manual_duration_seconds is not None else total_scene_effective, 1
    )
    project.updated_at = now
    if substantive:
        mark_script_downstream_for_review(session, project.id, episode_no)
    session.flush()
    response = _serialize_script(session, project, script)
    if substantive:
        _write_version(session, script, response, change_source, generation_id)
    session.flush()
    return response


def get_episode_script(project_id: str, episode_no: int) -> dict[str, Any] | None:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        script = _script_for_episode(session, project_id, episode_no)
        return _serialize_script(session, project, script) if script else None


def upsert_episode_script(project_id: str, episode_no: int, payload: ProjectEpisodeScriptPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        return _save_in_session(session, project, episode_no, payload)


def _generation_response(generation: ProjectScriptGeneration) -> dict[str, Any]:
    return {
        "id": generation.id, "project_id": generation.project_id, "episode_no": generation.episode_no,
        "generation_scope": generation.generation_scope, "target_scene_id": generation.target_scene_id,
        "target_block_ids": _loads(generation.target_block_ids, []), "rewrite_preset": generation.rewrite_preset,
        "instruction": generation.instruction, "base_script_version": generation.base_script_version,
        "base_script_revision": generation.base_script_revision, "input_snapshot": _loads(generation.input_snapshot, {}),
        "output_snapshot": _loads(generation.output_snapshot, {}), "status": generation.status,
        "client_request_id": generation.client_request_id, "model_config_id": generation.model_config_id,
        "model_name": generation.model_name, "elapsed_ms": generation.elapsed_ms,
        "adopted_at": generation.adopted_at.isoformat() if generation.adopted_at else None,
        "created_at": generation.created_at.isoformat(), "updated_at": generation.updated_at.isoformat(),
    }


def _generation_target(script_data: dict[str, Any] | None, payload: ScriptGenerationCreate) -> dict[str, Any]:
    if payload.generation_scope == "episode":
        return {"script": script_data}
    if not script_data:
        raise ValueError("正式剧本不存在")
    scene = next((item for item in script_data["scenes"] if item["id"] == payload.target_scene_id), None)
    if not scene:
        raise ValueError("目标场次不存在")
    if payload.generation_scope == "scene":
        return {"scene": scene}
    if not payload.target_block_ids:
        raise ValueError("请选择需要改写的内容块")
    order = [block["id"] for block in scene["blocks"]]
    try:
        positions = [order.index(block_id) for block_id in payload.target_block_ids]
    except ValueError as exc:
        raise ValueError("目标内容块不存在") from exc
    if len(set(positions)) != len(positions) or sorted(positions) != list(range(min(positions), max(positions) + 1)):
        raise ValueError("局部改写仅支持同一场次内连续内容块")
    return {"scene_id": scene["id"], "blocks": [scene["blocks"][index] for index in sorted(positions)]}


def _validate_generation_output(scope: str, output: dict[str, Any]) -> dict[str, Any]:
    def clean_block(raw: dict[str, Any]) -> dict[str, Any]:
        block = ScriptBlockPayload.model_validate(raw).model_dump(mode="json")
        block["id"] = None
        return block

    def clean_scene(raw: dict[str, Any]) -> dict[str, Any]:
        scene = ScriptScenePayload.model_validate(raw).model_dump(mode="json")
        scene["id"] = None
        scene["blocks"] = [clean_block(block) for block in raw.get("blocks", [])]
        return scene

    try:
        if scope == "episode":
            scenes = [clean_scene(item) for item in output.get("scenes", [])]
            if not scenes:
                raise ScriptValidationError("模型未返回有效场次")
            return {"title": output.get("title"), "scenes": scenes}
        if scope == "scene":
            raw = output.get("scene", output)
            return {"scene": clean_scene(raw)}
        blocks = [clean_block(item) for item in output.get("blocks", [])]
        if not blocks:
            raise ScriptValidationError("模型未返回有效内容块")
        return {"blocks": blocks}
    except ValidationError as exc:
        raise ScriptValidationError("模型输出不符合结构化剧本格式") from exc


async def generate_episode_script(project_id: str, episode_no: int, payload: ScriptGenerationCreate) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        existing = session.scalars(select(ProjectScriptGeneration).where(
            ProjectScriptGeneration.project_id == project_id,
            ProjectScriptGeneration.episode_no == episode_no,
            ProjectScriptGeneration.generation_scope == payload.generation_scope,
            ProjectScriptGeneration.client_request_id == payload.client_request_id,
        )).first()
        if existing:
            return _generation_response(existing)
        script = _script_for_episode(session, project_id, episode_no)
        script_data = _serialize_script(session, project, script) if script else None
        if script and (payload.base_script_version != script.version or payload.base_script_revision != script.revision):
            raise ScriptConflictError("正式剧本已变化，请刷新后重新生成")
        if not script and (payload.base_script_version is not None or payload.base_script_revision is not None):
            raise ScriptConflictError("正式剧本基准无效")
        content = session.scalars(select(ProjectEpisodeContent).where(
            ProjectEpisodeContent.project_id == project_id, ProjectEpisodeContent.episode_no == episode_no
        )).first()
        if payload.generation_scope == "episode" and (not content or not (content.detailed_content or "").strip()):
            raise ValueError("当前集还没有单集故事正文")
        target = _generation_target(script_data, payload)
        outline = session.scalars(select(ProjectEpisodeOutline).where(
            ProjectEpisodeOutline.project_id == project_id, ProjectEpisodeOutline.episode_no == episode_no
        )).first()
        story = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        worlds = session.scalars(select(ProjectWorldSnapshot).where(ProjectWorldSnapshot.project_id == project_id)).all()
        characters = session.scalars(select(ProjectCharacterSnapshot).where(ProjectCharacterSnapshot.project_id == project_id)).all()
        previous = session.scalars(select(ProjectEpisodeContent).where(
            ProjectEpisodeContent.project_id == project_id, ProjectEpisodeContent.episode_no == episode_no - 1
        )).first() if episode_no > 1 else None
        snapshot = {
            "project": project_to_response(project),
            "story_outline": story_outline_to_response(story) if story else None,
            "episode_outline": episode_outline_to_response(outline) if outline else None,
            "episode_content": episode_content_to_response(content) if content else None,
            "source_content_version": _source_content_version(content),
            "previous_episode_summary": previous.chapter_summary if previous else None,
            "world_snapshots": [world_snapshot_to_response(item) for item in worlds],
            "character_snapshots": [character_snapshot_to_response(item) for item in characters],
            "base_script": script_data,
            "target": target,
            "generation_scope": payload.generation_scope,
            "rewrite_preset": payload.rewrite_preset,
            "instruction": payload.instruction,
        }

    text_config = model_configs.get_enabled_config("text")
    if not text_config or text_config["last_test_status"] != "success":
        raise ValueError("请先配置并测试成功文本生成模型 API")
    expected = {
        "episode": "返回 JSON：{title, scenes:[{title,location,time_of_day,interior_exterior,character_snapshot_ids,story_purpose,blocks:[{block_type,character_snapshot_id,temporary_speaker_name,content,emotion,performance_note}]}]}",
        "scene": "返回 JSON：{scene:{title,location,time_of_day,interior_exterior,character_snapshot_ids,story_purpose,blocks:[...]}}",
        "blocks": "返回 JSON：{blocks:[{block_type,character_snapshot_id,temporary_speaker_name,content,emotion,performance_note}]}。只改写目标连续范围。",
    }[payload.generation_scope]
    prompt = f"你是中文短剧编剧。{expected}\n时间枚举 morning/day/dusk/night/other；内外景枚举 interior/exterior/mixed；内容类型 action/dialogue/voiceover/transition。只返回 JSON。\n上下文：{json.dumps(snapshot, ensure_ascii=False)}"
    started = time.perf_counter()
    output = await call_text_generation_api("生成可拍摄、顺序明确的结构化短剧剧本。", prompt, max_tokens=5000)
    normalized_output = _validate_generation_output(payload.generation_scope, output)
    elapsed = round((time.perf_counter() - started) * 1000)

    with get_session() as session:
        existing = session.scalars(select(ProjectScriptGeneration).where(
            ProjectScriptGeneration.project_id == project_id,
            ProjectScriptGeneration.episode_no == episode_no,
            ProjectScriptGeneration.generation_scope == payload.generation_scope,
            ProjectScriptGeneration.client_request_id == payload.client_request_id,
        )).first()
        if existing:
            return _generation_response(existing)
        now = now_utc()
        generation = ProjectScriptGeneration(
            id=str(uuid4()), project_id=project_id, episode_no=episode_no,
            generation_scope=payload.generation_scope, target_scene_id=payload.target_scene_id,
            target_block_ids=json.dumps(payload.target_block_ids), rewrite_preset=payload.rewrite_preset,
            instruction=payload.instruction, base_script_version=payload.base_script_version,
            base_script_revision=payload.base_script_revision,
            input_snapshot=json.dumps(snapshot, ensure_ascii=False),
            output_snapshot=json.dumps(normalized_output, ensure_ascii=False), status="candidate",
            client_request_id=payload.client_request_id, model_config_id=text_config.get("id"),
            model_name=text_config.get("model_name"), elapsed_ms=elapsed,
            created_at=now, updated_at=now,
        )
        session.add(generation)
        session.flush()
        candidates = session.scalars(select(ProjectScriptGeneration).where(
            ProjectScriptGeneration.project_id == project_id,
            ProjectScriptGeneration.episode_no == episode_no,
            ProjectScriptGeneration.status == "candidate",
        ).order_by(ProjectScriptGeneration.created_at.desc())).all()
        for stale in candidates[20:]:
            session.delete(stale)
        return _generation_response(generation)


def list_script_generations(project_id: str, episode_no: int) -> list[dict[str, Any]]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        rows = session.scalars(select(ProjectScriptGeneration).where(
            ProjectScriptGeneration.project_id == project_id,
            ProjectScriptGeneration.episode_no == episode_no,
        ).order_by(ProjectScriptGeneration.created_at.desc()).limit(100)).all()
        return [_generation_response(item) for item in rows]


def get_script_generation(project_id: str, episode_no: int, generation_id: str) -> dict[str, Any]:
    with get_session() as session:
        generation = session.get(ProjectScriptGeneration, generation_id)
        if not generation or generation.project_id != project_id or generation.episode_no != episode_no:
            raise ValueError("剧本候选不存在")
        return _generation_response(generation)


def _payload_from_script(data: dict[str, Any]) -> ProjectEpisodeScriptPayload:
    return ProjectEpisodeScriptPayload.model_validate({
        "revision": data["revision"], "title": data.get("title"),
        "manual_duration_seconds": data.get("manual_duration_seconds"),
        "scenes": [{
            "id": scene["id"], "title": scene.get("title"), "location": scene.get("location"),
            "time_of_day": scene.get("time_of_day"), "interior_exterior": scene.get("interior_exterior"),
            "character_snapshot_ids": scene.get("character_snapshot_ids", []),
            "manual_duration_seconds": scene.get("manual_duration_seconds"), "story_purpose": scene.get("story_purpose"),
            "blocks": [{key: block.get(key) for key in ("id", "block_type", "character_snapshot_id", "temporary_speaker_name", "content", "emotion", "performance_note")} for block in scene["blocks"]],
        } for scene in data["scenes"]],
    })


def adopt_script_generation(project_id: str, episode_no: int, generation_id: str, revision: ScriptRevisionPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        generation = session.get(ProjectScriptGeneration, generation_id)
        if not generation or generation.project_id != project_id or generation.episode_no != episode_no:
            raise ValueError("剧本候选不存在")
        if generation.status == "adopted":
            script = _script_for_episode(session, project_id, episode_no)
            return {"generation": _generation_response(generation), "script": _serialize_script(session, project, script)}
        if generation.status != "candidate":
            raise ScriptConflictError("该候选已放弃，不能采用")
        script = _script_for_episode(session, project_id, episode_no)
        if (script.revision if script else None) != revision.revision:
            raise ScriptConflictError("剧本已在候选生成后更新")
        if (script.version if script else None) != generation.base_script_version or (script.revision if script else None) != generation.base_script_revision:
            raise ScriptConflictError("候选基准已变化，请重新生成")
        output = _loads(generation.output_snapshot, {})
        if generation.generation_scope == "episode":
            payload_data = {"revision": revision.revision, "title": output.get("title"), "scenes": output["scenes"]}
        else:
            if not script:
                raise ScriptConflictError("正式剧本不存在")
            current = _serialize_script(session, project, script)
            payload = _payload_from_script(current)
            payload_data = payload.model_dump(mode="json")
            scene_index = next((index for index, item in enumerate(payload_data["scenes"]) if item["id"] == generation.target_scene_id), None)
            if scene_index is None:
                raise ScriptConflictError("目标场次已变化")
            if generation.generation_scope == "scene":
                replacement = output["scene"]
                replacement["id"] = generation.target_scene_id
                replacement["manual_duration_seconds"] = None
                replacement["blocks"] = [{**block, "id": None} for block in replacement.get("blocks", [])]
                payload_data["scenes"][scene_index] = replacement
            else:
                blocks = payload_data["scenes"][scene_index]["blocks"]
                target_ids = _loads(generation.target_block_ids, [])
                positions = [index for index, block in enumerate(blocks) if block.get("id") in target_ids]
                if len(positions) != len(target_ids) or positions != list(range(min(positions), max(positions) + 1)):
                    raise ScriptConflictError("目标内容块已变化")
                payload_data["scenes"][scene_index]["blocks"] = blocks[:min(positions)] + [{**block, "id": None} for block in output["blocks"]] + blocks[max(positions) + 1:]
        saved = _save_in_session(
            session, project, episode_no, ProjectEpisodeScriptPayload.model_validate(payload_data),
            change_source="generation_adopt", generation_id=generation.id,
        )
        generation.status = "adopted"
        generation.adopted_at = now_utc()
        generation.updated_at = generation.adopted_at
        session.flush()
        return {"generation": _generation_response(generation), "script": saved}


def discard_script_generation(project_id: str, episode_no: int, generation_id: str) -> dict[str, Any]:
    with get_session() as session:
        generation = session.get(ProjectScriptGeneration, generation_id)
        if not generation or generation.project_id != project_id or generation.episode_no != episode_no:
            raise ValueError("剧本候选不存在")
        if generation.status == "adopted":
            raise ScriptConflictError("已采用候选不能放弃")
        if generation.status == "candidate":
            generation.status = "discarded"
            generation.updated_at = now_utc()
            session.flush()
        return _generation_response(generation)


def _check_response(run: ProjectScriptCheckRun) -> dict[str, Any]:
    return {
        "id": run.id, "script_id": run.script_id, "script_version": run.script_version,
        "script_revision": run.script_revision, "mode": run.mode,
        "semantic_check_status": run.semantic_check_status, "issues": _loads(run.issues, []),
        "model_config_id": run.model_config_id, "model_name": run.model_name,
        "created_at": run.created_at.isoformat(),
    }


async def check_episode_script(project_id: str, episode_no: int, payload: ScriptCheckPayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        script = _script_for_episode(session, project_id, episode_no)
        if not script:
            raise ValueError("正式剧本不存在")
        if script.revision != payload.revision:
            raise ScriptConflictError("剧本已更新，请重新检查")
        data = _serialize_script(session, project, script)
        issues = list(data["validation_issues"])
        version, revision = script.version, script.revision
    semantic_status = "not_requested"
    text_config = model_configs.get_enabled_config("text") if payload.mode == "full" else None
    if payload.mode == "full":
        if not text_config or text_config.get("last_test_status") != "success":
            semantic_status = "failed"
        else:
            try:
                result = await call_text_generation_api(
                    "检查中文短剧剧本一致性，只返回 JSON。",
                    "返回 {issues:[{code,severity,message,scene_id,block_id,details}]}，severity 只能 warning 或 info。上下文：" + json.dumps(data, ensure_ascii=False),
                    max_tokens=1800,
                )
                for item in result.get("issues", []):
                    severity = item.get("severity") if item.get("severity") in {"warning", "info"} else "warning"
                    issues.append({
                        "code": str(item.get("code") or "semantic_issue"), "severity": severity,
                        "message": str(item.get("message") or "发现一致性风险"),
                        "scene_id": item.get("scene_id"), "block_id": item.get("block_id"),
                        "details": item.get("details") if isinstance(item.get("details"), dict) else {},
                    })
                semantic_status = "succeeded"
            except ValueError:
                semantic_status = "failed"
    with get_session() as session:
        script = session.get(ProjectEpisodeScript, data["id"])
        if not script or script.revision != revision:
            raise ScriptConflictError("剧本已更新，请重新检查")
        now = now_utc()
        run = ProjectScriptCheckRun(
            id=str(uuid4()), script_id=script.id, script_version=version, script_revision=revision,
            mode=payload.mode, semantic_check_status=semantic_status,
            issues=json.dumps(issues, ensure_ascii=False), model_config_id=text_config.get("id") if text_config else None,
            model_name=text_config.get("model_name") if text_config else None, created_at=now,
        )
        session.add(run)
        session.flush()
        return _check_response(run)


def _transition_status(project_id: str, episode_no: int, payload: ScriptRevisionPayload, status: str) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        script = _script_for_episode(session, project_id, episode_no)
        if not script:
            raise ValueError("正式剧本不存在")
        if script.revision != payload.revision:
            raise ScriptConflictError("剧本已更新，请刷新后重试")
        data = _serialize_script(session, project, script)
        errors = [item for item in data["validation_issues"] if item["severity"] == "error"]
        if errors:
            raise ScriptValidationError("剧本仍有结构错误", errors)
        script.status = status
        script.revision += 1
        script.updated_at = now_utc()
        if status == "confirmed":
            script.confirmed_at = script.updated_at
        session.flush()
        return _serialize_script(session, project, script)


def submit_episode_script(project_id: str, episode_no: int, payload: ScriptRevisionPayload) -> dict[str, Any]:
    return _transition_status(project_id, episode_no, payload, "pending_review")


def confirm_episode_script(project_id: str, episode_no: int, payload: ScriptRevisionPayload) -> dict[str, Any]:
    return _transition_status(project_id, episode_no, payload, "confirmed")


def list_episode_script_versions(project_id: str, episode_no: int) -> list[dict[str, Any]]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        script = _script_for_episode(session, project_id, episode_no)
        if not script:
            return []
        rows = session.scalars(select(ProjectEpisodeScriptVersion).where(
            ProjectEpisodeScriptVersion.script_id == script.id
        ).order_by(ProjectEpisodeScriptVersion.version.desc()).limit(100)).all()
        result = []
        for row in rows:
            snapshot = _loads(row.snapshot, {})
            result.append({
                "version": row.version, "source_content_version": row.source_content_version,
                "change_source": row.change_source, "generation_id": row.generation_id,
                "duration_seconds": snapshot.get("effective_duration_seconds", 0),
                "scene_count": len(snapshot.get("scenes", [])), "created_at": row.created_at.isoformat(),
            })
        return result


def get_episode_script_version(project_id: str, episode_no: int, version: int) -> dict[str, Any]:
    with get_session() as session:
        script = _script_for_episode(session, project_id, episode_no)
        if not script:
            raise ValueError("正式剧本不存在")
        row = session.scalars(select(ProjectEpisodeScriptVersion).where(
            ProjectEpisodeScriptVersion.script_id == script.id,
            ProjectEpisodeScriptVersion.version == version,
        )).first()
        if not row:
            raise ValueError("剧本历史版本不存在")
        return _loads(row.snapshot, {})
