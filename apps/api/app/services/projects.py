import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
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
    ReferenceStoryStructureDraft,
)
from app.models.schemas import (
    ProjectCharacterSnapshotUpdate,
    ProjectCopywritingPayload,
    ProjectCreate,
    ProjectEpisodeContentPayload,
    ProjectEpisodeOutlinePayload,
    ProjectEpisodeScriptPayload,
    ProjectStoryboardShotPayload,
    ProjectStoryOutlineResponse,
    ProjectStoryOutlinePayload,
    ReferenceStoryStructureApplyPayload,
    ReferenceStoryStructureExtractPayload,
    StoryOutlineGeneratePayload,
    StoryOutlineRewritePayload,
    ProjectUpdate,
    ProjectWorldSnapshotUpdate,
)
from app.services import model_configs


STORY_OUTLINE_FIELDS = (
    "logline",
    "story_background",
    "core_conflict",
    "main_goal",
    "story_start",
    "plot_structure",
    "reversals",
    "emotion_curve",
    "foreshadowing",
    "character_arcs",
    "ending_direction",
    "pacing_advice",
    "capacity_advice",
    "notes",
)

REFERENCE_DRAFT_FIELDS = (
    "story_type",
    "goal_model",
    "inciting_event_type",
    "conflict_model",
    "stage_structure",
    "reversal_mechanism",
    "emotion_curve",
    "foreshadowing_pattern",
    "ending_pattern",
    "adaptation_advice",
    "de_specificity_notes",
)

REWRITEABLE_STORY_FIELDS = {
    "story_background",
    "main_goal",
    "core_conflict",
    "plot_structure",
    "reversals",
    "emotion_curve",
    "foreshadowing",
    "ending_direction",
    "pacing_advice",
    "capacity_advice",
    "notes",
}


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


def _reference_outline_preview(draft: ReferenceStoryStructureDraft, user_requirements: str | None = None) -> ProjectStoryOutlinePayload:
    mapping = {
        "logline": draft.goal_model,
        "story_background": draft.story_type,
        "main_goal": draft.goal_model,
        "core_conflict": draft.conflict_model,
        "story_start": draft.inciting_event_type,
        "plot_structure": draft.stage_structure,
        "reversals": draft.reversal_mechanism,
        "emotion_curve": draft.emotion_curve,
        "foreshadowing": draft.foreshadowing_pattern,
        "character_arcs": None,
        "ending_direction": draft.ending_pattern,
        "pacing_advice": draft.adaptation_advice,
        "capacity_advice": draft.adaptation_advice,
        "notes": "\n\n".join(part for part in (draft.de_specificity_notes, user_requirements) if part),
    }
    normalized = {field: _normalize_optional_text(value) for field, value in mapping.items()}
    return ProjectStoryOutlinePayload(**normalized, status="draft")


def _reference_draft_to_response(draft: ReferenceStoryStructureDraft) -> dict[str, Any]:
    return {
        "id": draft.id,
        "project_id": draft.project_id,
        "source_type": draft.source_type,
        "source_filename": draft.source_filename,
        "source_text_excerpt": draft.source_text_excerpt,
        "story_type": draft.story_type,
        "goal_model": draft.goal_model,
        "inciting_event_type": draft.inciting_event_type,
        "conflict_model": draft.conflict_model,
        "stage_structure": draft.stage_structure,
        "reversal_mechanism": draft.reversal_mechanism,
        "emotion_curve": draft.emotion_curve,
        "foreshadowing_pattern": draft.foreshadowing_pattern,
        "ending_pattern": draft.ending_pattern,
        "adaptation_advice": draft.adaptation_advice,
        "de_specificity_notes": draft.de_specificity_notes,
        "validation_status": draft.validation_status,
        "validation_notes": draft.validation_notes,
        "status": draft.status,
        "outline_preview": _reference_outline_preview(draft).model_dump(),
        "created_at": draft.created_at.isoformat(),
        "updated_at": draft.updated_at.isoformat(),
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


def _outline_payload_dict(payload: ProjectStoryOutlinePayload) -> dict[str, Any]:
    return {field: getattr(payload, field) for field in STORY_OUTLINE_FIELDS} | {"status": payload.status}


def _outline_model_to_payload(outline: ProjectStoryOutline) -> ProjectStoryOutlinePayload:
    return ProjectStoryOutlinePayload(**{field: getattr(outline, field) for field in STORY_OUTLINE_FIELDS}, status=outline.status)


def _set_outline_fields(outline: ProjectStoryOutline, payload: ProjectStoryOutlinePayload) -> None:
    for field in STORY_OUTLINE_FIELDS:
        setattr(outline, field, getattr(payload, field))
    outline.status = payload.status


def _generated_outline_payload(data: dict[str, Any]) -> ProjectStoryOutlinePayload:
    normalized = {field: _normalize_optional_text(str(data.get(field))) if data.get(field) is not None else None for field in STORY_OUTLINE_FIELDS}
    return ProjectStoryOutlinePayload(**normalized, status="draft")


def _reference_draft_payload(data: dict[str, Any]) -> dict[str, str | None]:
    return {field: _normalize_optional_text(str(data.get(field))) if data.get(field) is not None else None for field in REFERENCE_DRAFT_FIELDS}


def _source_excerpt(source_text: str) -> str:
    normalized = " ".join(source_text.split())
    return normalized[:500]


def _rules_root() -> Path:
    return Path(__file__).resolve().parents[4] / "rules"


def _read_rule(name: str) -> str:
    path = _rules_root() / name
    if not path.exists():
        raise ValueError(f"规则文件不存在：{name}")
    return path.read_text(encoding="utf-8")


def _text_chat_completions_url(api_base_url: str) -> str:
    normalized_base_url = api_base_url.rstrip("/")
    if normalized_base_url.endswith("/chat/completions"):
        return normalized_base_url
    return f"{normalized_base_url}/chat/completions"


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            raise ValueError("模型响应不是可解析的 JSON")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("模型响应 JSON 必须是对象")
    return parsed


async def _call_text_generation_api(system_prompt: str, user_prompt: str, *, max_tokens: int = 1600) -> dict[str, Any]:
    text_config = model_configs.get_enabled_config("text")
    if not text_config or text_config["last_test_status"] != "success":
        raise ValueError("请先配置并测试成功文本生成模型 API")

    url = _text_chat_completions_url(text_config["api_base_url"])
    payload = {
        "model": text_config["model_name"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {text_config['api_key_secret']}"}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"文本生成接口返回错误状态：{exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise ValueError("文本生成接口无法访问，请检查 API 地址或网络连接") from exc

    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError("文本生成接口响应格式无法解析")
    return _extract_json_object(text)


def _project_context_summary(
    project: Project,
    world_snapshots: list[ProjectWorldSnapshot],
    character_snapshots: list[ProjectCharacterSnapshot],
    reference_draft: ReferenceStoryStructureDraft | None = None,
) -> str:
    world_summary = "未加载世界观"
    if world_snapshots:
        world_summary = "；".join(snapshot.name for snapshot in world_snapshots)
    character_summary = "未加载角色"
    if character_snapshots:
        character_summary = f"已加载 {len(character_snapshots)} 个角色：" + "、".join(snapshot.name for snapshot in character_snapshots[:6])
    reference_summary = "未使用参考框架"
    if reference_draft:
        reference_summary = f"使用参考框架：{reference_draft.story_type or reference_draft.goal_model or reference_draft.id}"
    return (
        f"项目：{project.title}；题材：{project.genre or '未设置'}；平台：{project.target_platform or '未设置'}；"
        f"集数：{project.episode_count}；单集时长：{project.episode_duration} 分钟；总时长：{project.total_duration} 分钟；"
        f"世界观：{world_summary}；角色：{character_summary}；{reference_summary}"
    )


def _outline_generation_prompt(
    project: Project,
    world_snapshots: list[ProjectWorldSnapshot],
    character_snapshots: list[ProjectCharacterSnapshot],
    reference_draft: ReferenceStoryStructureDraft | None,
    user_requirements: str | None,
) -> str:
    context = {
        "project": _project_to_response(project),
        "world_snapshots": [_world_snapshot_to_response(snapshot) for snapshot in world_snapshots],
        "character_snapshots": [_character_snapshot_to_response(snapshot) for snapshot in character_snapshots],
        "reference_structure": _reference_draft_to_response(reference_draft) if reference_draft else None,
        "user_requirements": user_requirements,
    }
    fields = ", ".join(STORY_OUTLINE_FIELDS)
    return (
        "请根据以下项目上下文生成整体故事大纲。只返回 JSON 对象，不要返回 Markdown。\n"
        f"JSON 字段必须包含：{fields}。\n"
        "所有字段值使用中文字符串；没有内容时使用空字符串。\n\n"
        f"{json.dumps(context, ensure_ascii=False)}"
    )


def _rewrite_prompt(project: Project, field: str, current_value: str, instruction: str) -> str:
    context = {
        "project": _project_to_response(project),
        "field": field,
        "current_value": current_value,
        "instruction": instruction,
    }
    return (
        "请局部改写指定故事大纲字段。只返回 JSON 对象，不要返回 Markdown。\n"
        "JSON 字段必须包含 value，value 为改写后的中文字符串。\n\n"
        f"{json.dumps(context, ensure_ascii=False)}"
    )


def _reference_extraction_prompt(project: Project, payload: ReferenceStoryStructureExtractPayload, retry_notes: str | None = None) -> str:
    context = {
        "project": _project_to_response(project),
        "source_type": payload.source_type,
        "source_filename": payload.source_filename,
        "source_text": payload.source_text,
        "user_requirements": payload.user_requirements,
        "retry_notes": retry_notes,
    }
    fields = ", ".join(REFERENCE_DRAFT_FIELDS)
    return (
        "请从参考故事中抽取可迁移叙事结构，并完成去具体化。只返回 JSON 对象，不要返回 Markdown。\n"
        f"JSON 字段必须包含：{fields}。\n"
        "不得出现原故事角色名、地名、组织名、专有名词、具体桥段、对白或原文句子；不要写摘要或改写。\n\n"
        f"{json.dumps(context, ensure_ascii=False)}"
    )


def _protected_terms(source_text: str) -> set[str]:
    terms = set(re.findall(r"《([^》]{2,30})》", source_text))
    known_terms = {
        "西游记",
        "唐僧",
        "孙悟空",
        "猪八戒",
        "沙僧",
        "白龙马",
        "如来",
        "观音",
        "西天",
        "取经",
        "火焰山",
    }
    for term in known_terms:
        if term in source_text:
            terms.add(term)
    terms.update(re.findall(r"\b[A-Z][A-Za-z0-9_]{2,}\b", source_text))
    return {term for term in terms if len(term.strip()) >= 2}


def _validate_reference_structure(data: dict[str, Any], source_text: str) -> tuple[str, str]:
    missing = [
        field
        for field in REFERENCE_DRAFT_FIELDS
        if data.get(field) is None or not _normalize_optional_text(str(data.get(field)))
    ]
    if missing:
        return "failed", f"抽取结果缺少必要结构字段：{', '.join(missing)}"

    serialized = json.dumps(data, ensure_ascii=False)
    leaked_terms = sorted(term for term in _protected_terms(source_text) if term and term in serialized)
    if leaked_terms:
        return "failed", f"抽取结果仍包含参考故事具体元素：{', '.join(leaked_terms[:8])}"

    if len(serialized) > max(len(source_text) * 0.6, 1200):
        return "failed", "抽取结果过长，疑似参考故事摘要或改写"

    return "passed", "去具体化校验通过"


def _apply_reference_to_outline(
    outline: ProjectStoryOutline,
    draft: ReferenceStoryStructureDraft,
    apply_mode: str,
    user_requirements: str | None,
) -> None:
    preview = _reference_outline_preview(draft, user_requirements)
    for field in STORY_OUTLINE_FIELDS:
        normalized = _normalize_optional_text(getattr(preview, field))
        if not normalized:
            continue
        if apply_mode == "overwrite" or not getattr(outline, field):
            setattr(outline, field, normalized)
    outline.status = "draft"


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


def update_project_world_snapshot(
    project_id: str,
    snapshot_id: str,
    payload: ProjectWorldSnapshotUpdate,
) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        snapshot = session.get(ProjectWorldSnapshot, snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise ValueError("项目世界观不存在")

        # 项目内微调只更新快照副本，不能回写 WorldBook 或 WorldEntry 原始资产。
        snapshot.name = payload.name
        snapshot.genre = payload.genre
        snapshot.snapshot_content = payload.snapshot_content
        snapshot.entry_snapshot_content = payload.entry_snapshot_content
        snapshot.updated_at = _now()
        project.updated_at = snapshot.updated_at
        _mark_project_downstream_for_review(session, project_id)
        session.flush()
        return _world_snapshot_to_response(snapshot)


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


def update_project_character_snapshot(
    project_id: str,
    snapshot_id: str,
    payload: ProjectCharacterSnapshotUpdate,
) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        snapshot = session.get(ProjectCharacterSnapshot, snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise ValueError("项目角色不存在")

        # 项目内微调只更新快照副本，不能回写 CharacterCard 原始资产。
        snapshot.name = payload.name
        snapshot.gender = payload.gender
        snapshot.role_type = payload.role_type
        snapshot.snapshot_content = payload.snapshot_content
        snapshot.visual_description = payload.visual_description
        snapshot.reference_image_url = payload.reference_image_url
        snapshot.reference_local_path = payload.reference_local_path
        snapshot.updated_at = _now()
        project.updated_at = snapshot.updated_at
        _mark_project_downstream_for_review(session, project_id)
        session.flush()
        return _character_snapshot_to_response(snapshot)


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

        _set_outline_fields(outline, payload)
        outline.updated_at = now
        project.updated_at = now
        _mark_story_downstream_for_review(session, project_id)
        session.flush()
        return _story_outline_to_response(outline)


async def generate_story_outline(project_id: str, payload: StoryOutlineGeneratePayload) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        world_snapshots = session.scalars(select(ProjectWorldSnapshot).where(ProjectWorldSnapshot.project_id == project_id)).all()
        character_snapshots = session.scalars(select(ProjectCharacterSnapshot).where(ProjectCharacterSnapshot.project_id == project_id)).all()
        reference_draft = None
        if payload.reference_draft_id:
            reference_draft = session.get(ReferenceStoryStructureDraft, payload.reference_draft_id)
            if not reference_draft or reference_draft.project_id != project_id:
                raise ValueError("参考框架草稿不存在")
            if reference_draft.validation_status != "passed":
                raise ValueError("参考框架草稿未通过去具体化校验，不能用于生成故事大纲")
        context_summary = _project_context_summary(project, world_snapshots, character_snapshots, reference_draft)
        prompt = _outline_generation_prompt(project, world_snapshots, character_snapshots, reference_draft, payload.user_requirements)

    system_prompt = _read_rule("story-outline-rule.md")
    data = await _call_text_generation_api(system_prompt, prompt)
    outline_payload = _generated_outline_payload(data)

    if payload.write_mode == "preview":
        return {
            "outline": _outline_payload_dict(outline_payload),
            "applied": False,
            "saved_outline": None,
            "context_summary": context_summary,
        }

    saved = upsert_story_outline(project_id, outline_payload)
    return {
        "outline": _outline_payload_dict(outline_payload),
        "applied": True,
        "saved_outline": saved,
        "context_summary": context_summary,
    }


async def rewrite_story_outline(project_id: str, payload: StoryOutlineRewritePayload) -> dict[str, Any]:
    if payload.field not in REWRITEABLE_STORY_FIELDS:
        raise ValueError("该故事大纲字段不支持局部改写")

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        if not outline:
            raise ValueError("整体故事大纲不存在")
        prompt = _rewrite_prompt(project, payload.field, payload.current_value, payload.instruction)

    system_prompt = _read_rule("story-outline-rule.md")
    data = await _call_text_generation_api(system_prompt, prompt, max_tokens=800)
    value = _normalize_optional_text(str(data.get("value"))) if data.get("value") is not None else None
    if not value:
        raise ValueError("局部改写结果为空")

    if payload.write_mode == "preview":
        return {"field": payload.field, "value": value, "applied": False, "saved_outline": None}

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        if not outline:
            raise ValueError("整体故事大纲不存在")
        setattr(outline, payload.field, value)
        outline.updated_at = _now()
        project.updated_at = outline.updated_at
        _mark_story_downstream_for_review(session, project_id)
        session.flush()
        return {"field": payload.field, "value": value, "applied": True, "saved_outline": _story_outline_to_response(outline)}


def list_reference_story_structure_drafts(project_id: str) -> list[dict[str, Any]]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        drafts = session.scalars(
            select(ReferenceStoryStructureDraft)
            .where(ReferenceStoryStructureDraft.project_id == project_id)
            .order_by(ReferenceStoryStructureDraft.updated_at.desc())
        ).all()
        return [_reference_draft_to_response(draft) for draft in drafts]


def get_reference_story_structure_draft(project_id: str, draft_id: str) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        draft = session.get(ReferenceStoryStructureDraft, draft_id)
        if not draft or draft.project_id != project_id:
            raise ValueError("参考框架草稿不存在")
        return _reference_draft_to_response(draft)


async def extract_reference_story_structure(project_id: str, payload: ReferenceStoryStructureExtractPayload) -> dict[str, Any]:
    if not _normalize_optional_text(payload.source_text):
        raise ValueError("请先上传或粘贴参考故事文本")

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        prompt = _reference_extraction_prompt(project, payload)

    system_prompt = _read_rule("story-structure-extraction-rule.md")
    data = await _call_text_generation_api(system_prompt, prompt, max_tokens=1800)
    validation_status, validation_notes = _validate_reference_structure(data, payload.source_text)

    if validation_status == "failed":
        retry_prompt = _reference_extraction_prompt(project, payload, validation_notes)
        data = await _call_text_generation_api(system_prompt, retry_prompt, max_tokens=1800)
        validation_status, validation_notes = _validate_reference_structure(data, payload.source_text)

    draft_values = _reference_draft_payload(data)
    now = _now()
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        draft = ReferenceStoryStructureDraft(
            id=str(uuid4()),
            project_id=project_id,
            source_type=payload.source_type,
            source_filename=payload.source_filename,
            source_text_excerpt=_source_excerpt(payload.source_text),
            validation_status=validation_status,
            validation_notes=validation_notes,
            status="draft",
            created_at=now,
            updated_at=now,
            **draft_values,
        )
        session.add(draft)
        session.flush()
        return _reference_draft_to_response(draft)


def apply_reference_story_structure_draft(
    project_id: str,
    draft_id: str,
    payload: ReferenceStoryStructureApplyPayload,
) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        draft = session.get(ReferenceStoryStructureDraft, draft_id)
        if not draft or draft.project_id != project_id:
            raise ValueError("参考框架草稿不存在")
        if draft.status == "discarded":
            raise ValueError("参考框架草稿已废弃")
        if draft.validation_status != "passed":
            raise ValueError("抽取结果未通过去具体化校验，不能应用到正式故事大纲")

        now = _now()
        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        if not outline:
            outline = ProjectStoryOutline(id=str(uuid4()), project_id=project_id, created_at=now, updated_at=now)
            session.add(outline)

        _apply_reference_to_outline(outline, draft, payload.apply_mode, payload.user_requirements)
        outline.updated_at = now
        draft.status = "applied"
        draft.updated_at = now
        project.updated_at = now
        _mark_story_downstream_for_review(session, project_id)
        session.flush()
        return _story_outline_to_response(outline)


def discard_reference_story_structure_draft(project_id: str, draft_id: str) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        draft = session.get(ReferenceStoryStructureDraft, draft_id)
        if not draft or draft.project_id != project_id:
            raise ValueError("参考框架草稿不存在")
        draft.status = "discarded"
        draft.updated_at = _now()
        session.flush()
        return _reference_draft_to_response(draft)


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
