"""故事大纲服务模块，处理整体故事大纲保存、AI 生成、局部改写和参考结构提取。"""
import json
import logging
import re
import time
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import (
    Project,
    ProjectCharacterSnapshot,
    ProjectStoryOutline,
    ProjectWorldSnapshot,
    ReferenceStoryStructureDraft,
)
from app.models.schemas import (
    ProjectStoryOutlinePayload,
    ReferenceStoryStructureApplyPayload,
    ReferenceStoryStructureExtractPayload,
    StoryOutlineAssistPatch,
    StoryOutlineAssistPayload,
    StoryOutlineGeneratePayload,
    StoryOutlineRewritePayload,
)
from app.services.project.common import (
    character_snapshot_to_response,
    mark_story_downstream_for_review,
    normalize_optional_text,
    now_utc,
    project_to_response,
    story_outline_to_response,
    world_snapshot_to_response,
)
from app.services.project.generation_common import (
    call_text_generation_api,
    outline_generation_prompt,
    project_context_summary,
    read_rule,
    reference_extraction_prompt,
    rewrite_prompt,
)


logger = logging.getLogger(__name__)

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

STORY_OUTLINE_ASSIST_REQUIRED_FIELDS = (
    "logline",
    "story_background",
    "main_goal",
    "core_conflict",
    "story_start",
    "ending_direction",
    "plot_structure",
    "reversals",
    "emotion_curve",
    "foreshadowing",
    "character_arcs",
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


def outline_payload_dict(payload: ProjectStoryOutlinePayload) -> dict[str, Any]:
    """将故事大纲 payload 转为普通字典，便于生成和改写流程复用。"""
    return {field: getattr(payload, field) for field in STORY_OUTLINE_FIELDS} | {"status": payload.status}


def outline_model_to_payload(outline: ProjectStoryOutline) -> ProjectStoryOutlinePayload:
    """将故事大纲数据库模型转换为可编辑 payload。"""
    return ProjectStoryOutlinePayload(**{field: getattr(outline, field) for field in STORY_OUTLINE_FIELDS}, status=outline.status)


def set_outline_fields(outline: ProjectStoryOutline, payload: ProjectStoryOutlinePayload) -> None:
    """把故事大纲 payload 写回数据库模型。"""
    for field in STORY_OUTLINE_FIELDS:
        setattr(outline, field, getattr(payload, field))
    outline.status = payload.status


def generated_outline_payload(data: dict[str, Any]) -> ProjectStoryOutlinePayload:
    """从模型生成结果构造故事大纲 payload，并补齐缺失字段。"""
    normalized = {field: normalize_optional_text(str(data.get(field))) if data.get(field) is not None else None for field in STORY_OUTLINE_FIELDS}
    return ProjectStoryOutlinePayload(**normalized, status="draft")


def story_outline_assist_patch(data: dict[str, Any]) -> StoryOutlineAssistPatch:
    """从辅助问答结果中解析可应用的故事大纲补丁。"""
    raw_patch = data.get("outline_patch")
    if not isinstance(raw_patch, dict):
        raw_patch = {}
    normalized = {
        field: normalize_optional_text(str(raw_patch.get(field))) if raw_patch.get(field) is not None else None
        for field in STORY_OUTLINE_FIELDS
    }
    return StoryOutlineAssistPatch(**normalized)


def merge_story_outline_patch(payload: ProjectStoryOutlinePayload, patch: StoryOutlineAssistPatch) -> ProjectStoryOutlinePayload:
    """合并故事大纲补丁，只覆盖模型明确返回的新内容。"""
    values = outline_payload_dict(payload)
    for field in STORY_OUTLINE_FIELDS:
        value = getattr(patch, field)
        if value is not None:
            values[field] = value
    return ProjectStoryOutlinePayload(**values)


def story_outline_assist_completion(payload: ProjectStoryOutlinePayload) -> dict[str, Any]:
    """计算故事大纲必填项完成度，帮助前端展示补全状态。"""
    completed_fields = [
        field
        for field in STORY_OUTLINE_ASSIST_REQUIRED_FIELDS
        if normalize_optional_text(getattr(payload, field))
    ]
    missing_fields = [field for field in STORY_OUTLINE_ASSIST_REQUIRED_FIELDS if field not in completed_fields]
    return {
        "required_fields": list(STORY_OUTLINE_ASSIST_REQUIRED_FIELDS),
        "completed_fields": completed_fields,
        "missing_fields": missing_fields,
        "is_complete": len(missing_fields) == 0,
    }


def story_outline_assist_notes(data: dict[str, Any]) -> dict[str, str]:
    """整理辅助问答返回的分字段建议说明。"""
    raw_notes = data.get("field_notes")
    if not isinstance(raw_notes, dict):
        return {}
    notes: dict[str, str] = {}
    for field, note in raw_notes.items():
        if field in STORY_OUTLINE_FIELDS and note is not None:
            normalized = normalize_optional_text(str(note))
            if normalized:
                notes[field] = normalized
    return notes


def story_outline_assist_next_focus(data: dict[str, Any]) -> list[str]:
    """整理下一步建议聚焦项，供作者继续完善大纲。"""
    raw_fields = data.get("next_focus_fields")
    if not isinstance(raw_fields, list):
        return []
    fields: list[str] = []
    for field in raw_fields:
        if isinstance(field, str) and field in STORY_OUTLINE_FIELDS and field not in fields:
            fields.append(field)
    return fields


def reference_draft_payload(data: dict[str, Any]) -> dict[str, str | None]:
    """从模型提取结果中整理参考结构草稿字段。"""
    return {field: normalize_optional_text(str(data.get(field))) if data.get(field) is not None else None for field in REFERENCE_DRAFT_FIELDS}


def source_excerpt(source_text: str) -> str:
    """截取参考故事原文片段，避免响应和存储内容过大。"""
    normalized = " ".join(source_text.split())
    return normalized[:500]


def reference_outline_preview(draft: ReferenceStoryStructureDraft, user_requirements: str | None = None) -> ProjectStoryOutlinePayload:
    """把参考结构草稿转换成可预览的故事大纲内容。"""
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
    normalized = {field: normalize_optional_text(value) for field, value in mapping.items()}
    return ProjectStoryOutlinePayload(**normalized, status="draft")


def reference_draft_to_response(draft: ReferenceStoryStructureDraft) -> dict[str, Any]:
    """序列化参考故事结构草稿响应。"""
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
        "outline_preview": reference_outline_preview(draft).model_dump(),
        "created_at": draft.created_at.isoformat(),
        "updated_at": draft.updated_at.isoformat(),
    }


def story_outline_assist_prompt(
    project: Project,
    world_snapshots: list[ProjectWorldSnapshot],
    character_snapshots: list[ProjectCharacterSnapshot],
    payload: StoryOutlineAssistPayload,
) -> str:
    """构建故事大纲辅助问答提示词，要求模型返回补丁和建议。"""
    completion = story_outline_assist_completion(payload.current_outline)
    context = {
        "action": payload.action,
        "project": project_to_response(project),
        "world_snapshots": [world_snapshot_to_response(snapshot) for snapshot in world_snapshots],
        "character_snapshots": [character_snapshot_to_response(snapshot) for snapshot in character_snapshots],
        "current_outline": outline_payload_dict(payload.current_outline),
        "completion": completion,
        "messages": [message.model_dump() for message in payload.messages],
        "user_message": payload.user_message,
        "required_fields": list(STORY_OUTLINE_ASSIST_REQUIRED_FIELDS),
    }
    return (
        "请根据以下上下文，以故事大纲 AI 协助创作身份继续引导用户。只返回 JSON 对象，不要返回 Markdown。\n"
        "JSON 字段必须包含：assistant_message、outline_patch、field_notes、next_focus_fields。\n"
        "outline_patch 只能包含允许的故事大纲文本字段，不得包含 status 或元数据字段。\n\n"
        f"{json.dumps(context, ensure_ascii=False)}"
    )


def protected_terms(source_text: str) -> set[str]:
    """提取参考文本中的受保护词，避免改写时直接复刻专有表达。"""
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


def validate_reference_structure(data: dict[str, Any], source_text: str) -> tuple[str, str]:
    """校验参考结构抽取结果，防止输出抄袭式或信息不足的结构。"""
    missing = [
        field
        for field in REFERENCE_DRAFT_FIELDS
        if data.get(field) is None or not normalize_optional_text(str(data.get(field)))
    ]
    if missing:
        return "failed", f"抽取结果缺少必要结构字段：{', '.join(missing)}"

    serialized = json.dumps(data, ensure_ascii=False)
    leaked_terms = sorted(term for term in protected_terms(source_text) if term and term in serialized)
    if leaked_terms:
        return "failed", f"抽取结果仍包含参考故事具体元素：{', '.join(leaked_terms[:8])}"

    if len(serialized) > max(len(source_text) * 0.6, 1200):
        return "failed", "抽取结果过长，疑似参考故事摘要或改写"

    return "passed", "去具体化校验通过"


def apply_reference_to_outline(
    outline: ProjectStoryOutline,
    draft: ReferenceStoryStructureDraft,
    apply_mode: str,
    user_requirements: str | None,
) -> None:
    """将参考结构按用户要求改写为当前项目的大纲预览。"""
    preview = reference_outline_preview(draft, user_requirements)
    for field in STORY_OUTLINE_FIELDS:
        normalized = normalize_optional_text(getattr(preview, field))
        if not normalized:
            continue
        if apply_mode == "overwrite" or not getattr(outline, field):
            setattr(outline, field, normalized)
    outline.status = "draft"


def get_story_outline(project_id: str) -> dict[str, Any] | None:
    """读取项目故事大纲，未创建时返回空结果。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        return story_outline_to_response(outline) if outline else None


def upsert_story_outline(project_id: str, payload: ProjectStoryOutlinePayload) -> dict[str, Any]:
    """创建或更新项目故事大纲，并标记下游内容需要复核。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        current_time = now_utc()
        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        if not outline:
            outline = ProjectStoryOutline(id=str(uuid4()), project_id=project_id, created_at=current_time, updated_at=current_time)
            session.add(outline)

        set_outline_fields(outline, payload)
        outline.updated_at = current_time
        project.updated_at = current_time
        mark_story_downstream_for_review(session, project_id)
        session.flush()
        return story_outline_to_response(outline)


async def generate_story_outline(project_id: str, payload: StoryOutlineGeneratePayload) -> dict[str, Any]:
    """调用文本模型生成项目整体故事大纲。"""
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
        context_summary = project_context_summary(project, world_snapshots, character_snapshots, reference_draft)
        prompt = outline_generation_prompt(
            project,
            world_snapshots,
            character_snapshots,
            reference_draft,
            payload.user_requirements,
            STORY_OUTLINE_FIELDS,
            reference_draft_to_response,
        )

    system_prompt = read_rule("story-outline-rule.md")
    data = await call_text_generation_api(system_prompt, prompt)
    outline_payload = generated_outline_payload(data)

    if payload.write_mode == "preview":
        return {
            "outline": outline_payload_dict(outline_payload),
            "applied": False,
            "saved_outline": None,
            "context_summary": context_summary,
        }

    saved = upsert_story_outline(project_id, outline_payload)
    return {
        "outline": outline_payload_dict(outline_payload),
        "applied": True,
        "saved_outline": saved,
        "context_summary": context_summary,
    }


async def rewrite_story_outline(project_id: str, payload: StoryOutlineRewritePayload) -> dict[str, Any]:
    """调用文本模型局部改写故事大纲指定字段。"""
    if payload.field not in REWRITEABLE_STORY_FIELDS:
        raise ValueError("该故事大纲字段不支持局部改写")

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        if not outline:
            raise ValueError("整体故事大纲不存在")
        prompt = rewrite_prompt(project, payload.field, payload.current_value, payload.instruction)

    system_prompt = read_rule("story-outline-rule.md")
    data = await call_text_generation_api(system_prompt, prompt, max_tokens=800)
    value = normalize_optional_text(str(data.get("value"))) if data.get("value") is not None else None
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
        outline.updated_at = now_utc()
        project.updated_at = outline.updated_at
        mark_story_downstream_for_review(session, project_id)
        session.flush()
        return {"field": payload.field, "value": value, "applied": True, "saved_outline": story_outline_to_response(outline)}


async def assist_story_outline(project_id: str, payload: StoryOutlineAssistPayload) -> dict[str, Any]:
    """调用文本模型根据对话辅助补全故事大纲。"""
    request_id = payload.client_request_id or uuid4().hex[:12]
    started_at = time.perf_counter()
    stage_timings: dict[str, int] = {}
    current_stage = "validate_payload"

    def elapsed_ms() -> int:
        return int((time.perf_counter() - started_at) * 1000)

    def mark_stage(stage: str) -> None:
        stage_timings[stage] = elapsed_ms()

    try:
        logger.info(
            "story_outline_assist.start request_id=%s project_id=%s action=%s",
            request_id,
            project_id,
            payload.action,
        )
        if payload.action == "reply" and not payload.user_message:
            raise ValueError("请先输入回复内容")
        mark_stage(current_stage)

        current_stage = "load_context"
        with get_session() as session:
            project = session.get(Project, project_id)
            if not project:
                raise ValueError("项目不存在")
            world_snapshots = session.scalars(select(ProjectWorldSnapshot).where(ProjectWorldSnapshot.project_id == project_id)).all()
            character_snapshots = session.scalars(select(ProjectCharacterSnapshot).where(ProjectCharacterSnapshot.project_id == project_id)).all()
            mark_stage(current_stage)

            current_stage = "build_prompt"
            prompt = story_outline_assist_prompt(project, world_snapshots, character_snapshots, payload)
            mark_stage(current_stage)

        current_stage = "read_rule"
        system_prompt = read_rule("story-outline-assistant-rule.md")
        mark_stage(current_stage)

        current_stage = "model_call"
        logger.info(
            "story_outline_assist.model_call.start request_id=%s project_id=%s elapsed_ms=%s",
            request_id,
            project_id,
            elapsed_ms(),
        )
        data = await call_text_generation_api(system_prompt, prompt, max_tokens=1400)
        mark_stage(current_stage)
        logger.info(
            "story_outline_assist.model_call.done request_id=%s project_id=%s elapsed_ms=%s",
            request_id,
            project_id,
            elapsed_ms(),
        )

        current_stage = "parse_response"
        assistant_message = normalize_optional_text(str(data.get("assistant_message"))) if data.get("assistant_message") is not None else None
        if not assistant_message:
            raise ValueError("AI 协助响应缺少引导内容")

        patch = story_outline_assist_patch(data)
        merged_outline = merge_story_outline_patch(payload.current_outline, patch)
        completion = story_outline_assist_completion(merged_outline)
        field_notes = story_outline_assist_notes(data)
        next_focus_fields = story_outline_assist_next_focus(data)
        mark_stage(current_stage)

        total_elapsed_ms = elapsed_ms()
        logger.info(
            "story_outline_assist.complete request_id=%s project_id=%s elapsed_ms=%s stage_timings=%s",
            request_id,
            project_id,
            total_elapsed_ms,
            stage_timings,
        )
        return {
            "assistant_message": assistant_message,
            "outline_patch": patch.model_dump(exclude_none=True),
            "completion": completion,
            "field_notes": field_notes,
            "next_focus_fields": next_focus_fields,
            "request_id": request_id,
            "elapsed_ms": total_elapsed_ms,
            "stage_timings": stage_timings,
        }
    except ValueError as exc:
        logger.warning(
            "story_outline_assist.failed request_id=%s project_id=%s stage=%s elapsed_ms=%s stage_timings=%s error=%s",
            request_id,
            project_id,
            current_stage,
            elapsed_ms(),
            stage_timings,
            exc,
            exc_info=True,
        )
        message = str(exc)
        if "请求编号" not in message:
            message = f"{message}（请求编号：{request_id}）"
        raise ValueError(message) from exc
    except Exception as exc:
        logger.exception(
            "story_outline_assist.unexpected_failed request_id=%s project_id=%s stage=%s elapsed_ms=%s stage_timings=%s",
            request_id,
            project_id,
            current_stage,
            elapsed_ms(),
            stage_timings,
        )
        raise ValueError(f"AI 协助失败，请稍后重试（请求编号：{request_id}）") from exc


def list_reference_story_structure_drafts(project_id: str) -> list[dict[str, Any]]:
    """列出项目内参考故事结构草稿。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        drafts = session.scalars(
            select(ReferenceStoryStructureDraft)
            .where(ReferenceStoryStructureDraft.project_id == project_id)
            .order_by(ReferenceStoryStructureDraft.updated_at.desc())
        ).all()
        return [reference_draft_to_response(draft) for draft in drafts]


def get_reference_story_structure_draft(project_id: str, draft_id: str) -> dict[str, Any]:
    """读取单个参考故事结构草稿。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        draft = session.get(ReferenceStoryStructureDraft, draft_id)
        if not draft or draft.project_id != project_id:
            raise ValueError("参考框架草稿不存在")
        return reference_draft_to_response(draft)


async def extract_reference_story_structure(project_id: str, payload: ReferenceStoryStructureExtractPayload) -> dict[str, Any]:
    """从参考文本中抽取可复用故事结构草稿。"""
    if not normalize_optional_text(payload.source_text):
        raise ValueError("请先上传或粘贴参考故事文本")

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        prompt = reference_extraction_prompt(project, payload)

    system_prompt = read_rule("story-structure-extraction-rule.md")
    data = await call_text_generation_api(system_prompt, prompt, max_tokens=1800)
    validation_status, validation_notes = validate_reference_structure(data, payload.source_text)

    if validation_status == "failed":
        retry_prompt = reference_extraction_prompt(project, payload, validation_notes)
        data = await call_text_generation_api(system_prompt, retry_prompt, max_tokens=1800)
        validation_status, validation_notes = validate_reference_structure(data, payload.source_text)

    draft_values = reference_draft_payload(data)
    current_time = now_utc()
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        draft = ReferenceStoryStructureDraft(
            id=str(uuid4()),
            project_id=project_id,
            source_type=payload.source_type,
            source_filename=payload.source_filename,
            source_text_excerpt=source_excerpt(payload.source_text),
            validation_status=validation_status,
            validation_notes=validation_notes,
            status="draft",
            created_at=current_time,
            updated_at=current_time,
            **draft_values,
        )
        session.add(draft)
        session.flush()
        return reference_draft_to_response(draft)


def apply_reference_story_structure_draft(
    project_id: str,
    draft_id: str,
    payload: ReferenceStoryStructureApplyPayload,
) -> dict[str, Any]:
    """把参考结构草稿应用为当前项目故事大纲。"""
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

        current_time = now_utc()
        outline = session.scalars(select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)).first()
        if not outline:
            outline = ProjectStoryOutline(id=str(uuid4()), project_id=project_id, created_at=current_time, updated_at=current_time)
            session.add(outline)

        apply_reference_to_outline(outline, draft, payload.apply_mode, payload.user_requirements)
        outline.updated_at = current_time
        draft.status = "applied"
        draft.updated_at = current_time
        project.updated_at = current_time
        mark_story_downstream_for_review(session, project_id)
        session.flush()
        return story_outline_to_response(outline)


def discard_reference_story_structure_draft(project_id: str, draft_id: str) -> dict[str, Any]:
    """丢弃参考结构草稿，仅影响当前项目草稿状态。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        draft = session.get(ReferenceStoryStructureDraft, draft_id)
        if not draft or draft.project_id != project_id:
            raise ValueError("参考框架草稿不存在")
        draft.status = "discarded"
        draft.updated_at = now_utc()
        session.flush()
        return reference_draft_to_response(draft)
