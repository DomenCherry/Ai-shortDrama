"""单集正文服务模块，处理正文保存、AI 候选生成和安全采用。"""
import json
import time
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update

from app.core.db import get_session
from app.models.db_models import (
    EpisodeContentGenerationVersion,
    Project,
    ProjectCharacterSnapshot,
    ProjectEpisodeContent,
    ProjectEpisodeOutline,
    ProjectStoryOutline,
    ProjectWorldSnapshot,
)
from app.models.schemas import (
    EpisodeContentGenerationCreate,
    EpisodeContentGenerationUpdate,
    ProjectEpisodeContentPayload,
)
from app.services import model_configs
from app.services.project.generation_common import call_text_generation_raw, read_rule
from app.services.project.common import (
    character_snapshot_to_response,
    count_content_characters,
    episode_content_generation_to_response,
    episode_content_to_response,
    episode_outline_to_response,
    mark_episode_content_downstream_for_review,
    now_utc,
    project_to_response,
    story_outline_to_response,
    validate_episode_no,
    world_snapshot_to_response,
)


def get_episode_content(project_id: str, episode_no: int) -> dict[str, Any] | None:
    """读取指定集数的详细故事正文。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        content = session.scalars(
            select(ProjectEpisodeContent).where(
                ProjectEpisodeContent.project_id == project_id,
                ProjectEpisodeContent.episode_no == episode_no,
            )
        ).first()
        return episode_content_to_response(content) if content else None


def upsert_episode_content(project_id: str, episode_no: int, payload: ProjectEpisodeContentPayload) -> dict[str, Any]:
    """创建或更新指定集数正文，并同步字数和下游复核状态。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        current_time = now_utc()
        content = session.scalars(
            select(ProjectEpisodeContent).where(
                ProjectEpisodeContent.project_id == project_id,
                ProjectEpisodeContent.episode_no == episode_no,
            )
        ).first()
        if not content:
            content = ProjectEpisodeContent(
                id=str(uuid4()), project_id=project_id, episode_no=episode_no, created_at=current_time, updated_at=current_time
            )
            session.add(content)

        content.title = payload.title
        content.detailed_content = payload.detailed_content
        content.chapter_summary = payload.chapter_summary
        content.hook = payload.hook
        content.key_beats = payload.key_beats
        content.word_count = count_content_characters(payload.detailed_content)
        content.previous_context_summary = payload.previous_context_summary
        content.quality_check_notes = payload.quality_check_notes
        content.status = payload.status
        content.updated_at = current_time
        project.updated_at = current_time
        mark_episode_content_downstream_for_review(session, project_id, episode_no)
        session.flush()
        return episode_content_to_response(content)


def _get_generation(session, project_id: str, episode_no: int, generation_id: str) -> EpisodeContentGenerationVersion:
    generation = session.get(EpisodeContentGenerationVersion, generation_id)
    if not generation or generation.project_id != project_id or generation.episode_no != episode_no:
        raise ValueError("正文候选版本不存在")
    return generation


def _generation_prompt(snapshot: dict[str, Any], instruction: str | None) -> str:
    """把固定上下文快照组装为模型输入，不包含当前正式正文。"""
    payload = {
        "task": "基于给定上下文创作当前集完整的小说化故事正文",
        "project": snapshot["project"],
        "story_outline": snapshot["story_outline"],
        "episode_outline": snapshot["episode_outline"],
        "world_snapshots": snapshot["world_snapshots"],
        "character_snapshots": snapshot["character_snapshots"],
        "previous_episode_summary": snapshot["previous_episode_summary"],
        "target_chinese_characters": snapshot["target_chinese_characters"],
        "user_instruction": instruction or "无额外要求",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


async def generate_episode_content(
    project_id: str,
    episode_no: int,
    payload: EpisodeContentGenerationCreate,
) -> dict[str, Any]:
    """生成并持久化候选稿；相同请求 ID 直接返回已有结果。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)

        existing = session.scalars(
            select(EpisodeContentGenerationVersion).where(
                EpisodeContentGenerationVersion.project_id == project_id,
                EpisodeContentGenerationVersion.episode_no == episode_no,
                EpisodeContentGenerationVersion.client_request_id == payload.client_request_id,
            )
        ).first()
        if existing:
            return episode_content_generation_to_response(existing)

        episode_outline = session.scalars(
            select(ProjectEpisodeOutline).where(
                ProjectEpisodeOutline.project_id == project_id,
                ProjectEpisodeOutline.episode_no == episode_no,
            )
        ).first()
        if not episode_outline or not any(
            (episode_outline.title, episode_outline.synopsis, episode_outline.hook, episode_outline.conflict,
             episode_outline.reversal, episode_outline.cliffhanger)
        ):
            raise ValueError("请先完善并保存本集分集大纲，再生成正文")

        story_outline = session.scalars(
            select(ProjectStoryOutline).where(ProjectStoryOutline.project_id == project_id)
        ).first()
        world_snapshots = session.scalars(
            select(ProjectWorldSnapshot).where(ProjectWorldSnapshot.project_id == project_id)
        ).all()
        character_snapshots = session.scalars(
            select(ProjectCharacterSnapshot).where(ProjectCharacterSnapshot.project_id == project_id)
        ).all()
        current_content = session.scalars(
            select(ProjectEpisodeContent).where(
                ProjectEpisodeContent.project_id == project_id,
                ProjectEpisodeContent.episode_no == episode_no,
            )
        ).first()
        previous_content = None
        if episode_no > 1:
            previous_content = session.scalars(
                select(ProjectEpisodeContent).where(
                    ProjectEpisodeContent.project_id == project_id,
                    ProjectEpisodeContent.episode_no == episode_no - 1,
                )
            ).first()

        duration = episode_outline.duration_minutes or project.episode_duration or 1
        target_min = max(60, round(duration * 600))
        target_max = max(target_min, round(duration * 900))
        snapshot = {
            "project": project_to_response(project),
            "story_outline": story_outline_to_response(story_outline) if story_outline else None,
            "episode_outline": episode_outline_to_response(episode_outline),
            "world_snapshots": [world_snapshot_to_response(item) for item in world_snapshots],
            "character_snapshots": [character_snapshot_to_response(item) for item in character_snapshots],
            "previous_episode_summary": previous_content.chapter_summary if previous_content else None,
            "target_chinese_characters": {"min": target_min, "max": target_max},
            "current_content_updated_at": current_content.updated_at.isoformat() if current_content else None,
            "has_existing_content": bool(current_content and current_content.detailed_content),
        }

    text_config = model_configs.get_enabled_config("text")
    if not text_config or text_config["last_test_status"] != "success":
        raise ValueError("请先配置并测试成功文本生成模型 API")

    started_at = time.perf_counter()
    system_prompt = read_rule("episode-content-writing-rule.md")
    max_tokens = min(3600, max(1600, round(target_max * 1.6)))
    response = await call_text_generation_raw(
        system_prompt,
        _generation_prompt(snapshot, payload.instruction),
        max_tokens=max_tokens,
    )
    elapsed_ms = round((time.perf_counter() - started_at) * 1000)
    if response.finish_reason in {"length", "max_tokens"}:
        raise ValueError("候选稿生成不完整，请重试")
    output_text = response.content.strip()
    if not output_text:
        raise ValueError("正文生成结果为空，请调整创作要求后重试")

    with get_session() as session:
        existing = session.scalars(
            select(EpisodeContentGenerationVersion).where(
                EpisodeContentGenerationVersion.project_id == project_id,
                EpisodeContentGenerationVersion.episode_no == episode_no,
                EpisodeContentGenerationVersion.client_request_id == payload.client_request_id,
            )
        ).first()
        if existing:
            return episode_content_generation_to_response(existing)

        current_time = now_utc()
        generation = EpisodeContentGenerationVersion(
            id=str(uuid4()),
            project_id=project_id,
            episode_no=episode_no,
            instruction=payload.instruction,
            input_snapshot=json.dumps(snapshot, ensure_ascii=False),
            output_text=output_text,
            status="candidate",
            client_request_id=payload.client_request_id,
            model_config_id=text_config.get("id"),
            model_name=text_config.get("model_name"),
            elapsed_ms=elapsed_ms,
            created_at=current_time,
            updated_at=current_time,
        )
        session.add(generation)
        session.flush()
        return episode_content_generation_to_response(generation)


def list_episode_content_generations(project_id: str, episode_no: int) -> list[dict[str, Any]]:
    """读取最近十个生成版本，供刷新恢复与简洁历史选择。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        generations = session.scalars(
            select(EpisodeContentGenerationVersion)
            .where(
                EpisodeContentGenerationVersion.project_id == project_id,
                EpisodeContentGenerationVersion.episode_no == episode_no,
            )
            .order_by(EpisodeContentGenerationVersion.created_at.desc())
            .limit(10)
        ).all()
        return [episode_content_generation_to_response(item) for item in generations]


def update_episode_content_generation(
    project_id: str,
    episode_no: int,
    generation_id: str,
    payload: EpisodeContentGenerationUpdate,
) -> dict[str, Any]:
    """保存候选稿编辑，仅允许修改仍处于候选状态的版本。"""
    with get_session() as session:
        generation = _get_generation(session, project_id, episode_no, generation_id)
        if generation.status != "candidate":
            raise ValueError("该候选版本已处理，不能继续编辑")
        generation.output_text = payload.output_text
        generation.updated_at = now_utc()
        session.flush()
        return episode_content_generation_to_response(generation)


def adopt_episode_content_generation(project_id: str, episode_no: int, generation_id: str) -> dict[str, Any]:
    """采用候选稿，校验正文未被并发修改后原子更新正式正文。"""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")
        validate_episode_no(project, episode_no)
        generation = _get_generation(session, project_id, episode_no, generation_id)
        if generation.status != "candidate":
            raise ValueError("该候选版本已处理，不能重复采用")

        content = session.scalars(
            select(ProjectEpisodeContent).where(
                ProjectEpisodeContent.project_id == project_id,
                ProjectEpisodeContent.episode_no == episode_no,
            )
        ).first()
        snapshot = json.loads(generation.input_snapshot)
        expected_updated_at = snapshot.get("current_content_updated_at")
        actual_updated_at = content.updated_at.isoformat() if content else None
        if expected_updated_at != actual_updated_at:
            raise ValueError("当前正文已在候选稿生成后更新，请重新生成候选稿")

        current_time = now_utc()
        episode_outline = session.scalars(
            select(ProjectEpisodeOutline).where(
                ProjectEpisodeOutline.project_id == project_id,
                ProjectEpisodeOutline.episode_no == episode_no,
            )
        ).first()
        if not content:
            content = ProjectEpisodeContent(
                id=str(uuid4()),
                project_id=project_id,
                episode_no=episode_no,
                created_at=current_time,
                updated_at=current_time,
            )
            session.add(content)
        content.title = episode_outline.title if episode_outline else content.title
        content.detailed_content = generation.output_text
        content.chapter_summary = None
        content.quality_check_notes = None
        content.word_count = count_content_characters(generation.output_text)
        content.previous_context_summary = snapshot.get("previous_episode_summary")
        content.status = "draft"
        content.updated_at = current_time
        project.updated_at = current_time
        generation.status = "adopted"
        generation.adopted_at = current_time
        generation.updated_at = current_time
        session.execute(
            update(EpisodeContentGenerationVersion)
            .where(
                EpisodeContentGenerationVersion.project_id == project_id,
                EpisodeContentGenerationVersion.episode_no == episode_no,
                EpisodeContentGenerationVersion.id != generation.id,
                EpisodeContentGenerationVersion.status == "candidate",
            )
            .values(status="discarded", updated_at=current_time)
        )
        mark_episode_content_downstream_for_review(session, project_id, episode_no)
        session.flush()
        return {
            "generation": episode_content_generation_to_response(generation),
            "content": episode_content_to_response(content),
        }


def discard_episode_content_generation(project_id: str, episode_no: int, generation_id: str) -> dict[str, Any]:
    """放弃候选稿，保留记录用于历史追溯。"""
    with get_session() as session:
        generation = _get_generation(session, project_id, episode_no, generation_id)
        if generation.status != "candidate":
            raise ValueError("该候选版本已处理")
        generation.status = "discarded"
        generation.updated_at = now_utc()
        session.flush()
        return episode_content_generation_to_response(generation)
