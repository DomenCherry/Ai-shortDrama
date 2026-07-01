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
from app.services.project.generation_common import call_text_generation_raw, read_rule, rules_root
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
from app.services.user_skills import ensure_user_skill_enabled


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


GENERATION_TYPE_LABELS = {
    "create": "正文创作",
    "continue": "续写",
    "polish": "润色",
}


def _clean_content(value: str | None) -> str:
    return (value or "").strip()


def _generation_system_prompt(generation_type: str) -> str:
    base_rule = read_rule("episode-content-writing-rule.md")
    humanizer_skill_path = rules_root().parent / "runtime-skills" / "humanizer-zh" / "SKILL.md"
    if not humanizer_skill_path.exists():
        # 正文生成依赖 Humanizer-zh 降低 AI 腔；缺少规则时宁可失败，也不要生成风格不可控的候选稿。
        raise ValueError("Humanizer-zh skill 未安装，请先安装到项目 runtime-skills/humanizer-zh")
    humanizer_skill = humanizer_skill_path.read_text(encoding="utf-8")
    humanizer_adaptation_rule = read_rule("episode-content-humanizer-rule.md")
    operation_rule = {
        "create": "本次任务：创作当前集完整候选正文。不要引用或改写当前正式正文。",
        "continue": (
            "本次任务：基于当前正文末尾续写，并返回“当前正文 + 新增续写”的完整候选正文。"
            "不要重写已存在正文，不要省略当前正文。"
        ),
        "polish": (
            "本次任务：润色当前正文全文，并返回完整润色候选正文。"
            "不要新增关键剧情，不要改变事实、人物关系、事件顺序和结尾信息。"
        ),
    }[generation_type]
    return "\n\n".join(
        [
            base_rule,
            "# Humanizer-zh 原始 skill 规则\n\n以下规则来自项目内安装的 runtime-skills/humanizer-zh/SKILL.md。只采用其去 AI 味原则；输出格式以本服务规则为准。",
            humanizer_skill,
            humanizer_adaptation_rule,
            operation_rule,
        ]
    )


def _generation_prompt(snapshot: dict[str, Any], instruction: str | None, generation_type: str) -> str:
    """把上下文快照组装为模型输入；create 不把当前正式正文作为重写输入。"""
    task = {
        "create": "基于给定上下文创作当前集完整的小说化故事正文",
        "continue": "基于当前正文末尾续写，返回当前正文加续写内容后的完整候选正文",
        "polish": "基于去 AI 味规则润色当前正文全文，返回完整候选正文",
    }[generation_type]
    payload = {
        "task": task,
        "generation_type": generation_type,
        "project": snapshot["project"],
        "story_outline": snapshot["story_outline"],
        "episode_outline": snapshot["episode_outline"],
        "world_snapshots": snapshot["world_snapshots"],
        "character_snapshots": snapshot["character_snapshots"],
        "previous_episode_summary": snapshot["previous_episode_summary"],
        "target_chinese_characters": snapshot["target_chinese_characters"],
        "user_instruction": instruction or "无额外要求",
    }
    if generation_type in {"continue", "polish"}:
        payload["current_content"] = snapshot.get("current_content", {})
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _max_tokens_for_generation(generation_type: str, target_max: int, current_content_text: str | None = None) -> int:
    if generation_type == "polish":
        return min(6000, max(1600, round(max(target_max, len(current_content_text or "")) * 1.8)))
    if generation_type == "continue":
        return min(6000, max(1600, round(max(target_max, len(current_content_text or "")) * 1.8)))
    return min(3600, max(1600, round(target_max * 1.6)))


def _truncated_generation_message(generation_type: str) -> str:
    if generation_type == "continue":
        return "续写候选稿生成不完整，请重试"
    if generation_type == "polish":
        return "润色候选稿生成不完整，请重试"
    return "候选稿生成不完整，请重试"


async def generate_episode_content(
    project_id: str,
    episode_no: int,
    payload: EpisodeContentGenerationCreate,
) -> dict[str, Any]:
    """生成并持久化候选稿；相同请求 ID 直接返回已有结果。"""
    ensure_user_skill_enabled("short-drama-creator")

    generation_type = payload.generation_type
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
            # client_request_id 保证前端重试不会重复创建候选稿，避免用户误采用过期或重复版本。
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
        current_content_text = _clean_content(current_content.detailed_content if current_content else None)
        if generation_type in {"continue", "polish"} and not current_content_text:
            # 续写和润色必须以当前正式正文为基准，空正文会让模型脱离用户已确认内容。
            label = GENERATION_TYPE_LABELS[generation_type]
            raise ValueError(f"{label}需要当前正文非空，请先填写并保存正文")
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
            "generation_type": generation_type,
            "humanizer": {
                "source": "op7418/Humanizer-zh",
                "source_url": "https://github.com/op7418/Humanizer-zh",
                "license": "MIT",
                "adaptation_rule": "episode-content-humanizer-rule.md",
                "mode": "single_pass_fusion",
            },
            "project": project_to_response(project),
            "story_outline": story_outline_to_response(story_outline) if story_outline else None,
            "episode_outline": episode_outline_to_response(episode_outline),
            "world_snapshots": [world_snapshot_to_response(item) for item in world_snapshots],
            "character_snapshots": [character_snapshot_to_response(item) for item in character_snapshots],
            "previous_episode_summary": previous_content.chapter_summary if previous_content else None,
            "target_chinese_characters": {"min": target_min, "max": target_max},
            "current_content_updated_at": current_content.updated_at.isoformat() if current_content else None,
            "has_existing_content": bool(current_content_text),
        }
        if generation_type in {"continue", "polish"}:
            snapshot["current_content"] = {
                "word_count": count_content_characters(current_content_text),
                "updated_at": current_content.updated_at.isoformat() if current_content else None,
                "text": current_content_text,
            }

    text_config = model_configs.get_enabled_config("text")
    if not text_config or text_config["last_test_status"] != "success":
        raise ValueError("请先配置并测试成功文本生成模型 API")

    started_at = time.perf_counter()
    system_prompt = _generation_system_prompt(generation_type)
    max_tokens = _max_tokens_for_generation(generation_type, target_max, current_content_text)
    response = await call_text_generation_raw(
        system_prompt,
        _generation_prompt(snapshot, payload.instruction, generation_type),
        max_tokens=max_tokens,
    )
    elapsed_ms = round((time.perf_counter() - started_at) * 1000)
    if response.finish_reason in {"length", "max_tokens"}:
        raise ValueError(_truncated_generation_message(generation_type))
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
            generation_type=generation_type,
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
            # 候选稿采用前校验生成时的正文快照，防止覆盖用户在生成后手工修改的正式正文。
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
        # 同一集只允许一个候选被采用，其余候选标记废弃，避免多个候选同时代表“最新正式来源”。
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
