import json
import re
from pathlib import Path
from typing import Any

import httpx

from app.models.db_models import Project, ProjectCharacterSnapshot, ProjectWorldSnapshot, ReferenceStoryStructureDraft
from app.services import model_configs
from app.services.project.common import character_snapshot_to_response, project_to_response, world_snapshot_to_response


def rules_root() -> Path:
    return Path(__file__).resolve().parents[5] / "rules"


def read_rule(name: str) -> str:
    path = rules_root() / name
    if not path.exists():
        raise ValueError(f"规则文件不存在：{name}")
    return path.read_text(encoding="utf-8")


def text_chat_completions_url(api_base_url: str) -> str:
    normalized_base_url = api_base_url.rstrip("/")
    if normalized_base_url.endswith("/chat/completions"):
        return normalized_base_url
    return f"{normalized_base_url}/chat/completions"


def extract_json_object(text: str) -> dict[str, Any]:
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


async def call_text_generation_api(system_prompt: str, user_prompt: str, *, max_tokens: int = 1600) -> dict[str, Any]:
    text_config = model_configs.get_enabled_config("text")
    if not text_config or text_config["last_test_status"] != "success":
        raise ValueError("请先配置并测试成功文本生成模型 API")

    url = text_chat_completions_url(text_config["api_base_url"])
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
    return extract_json_object(text)


def project_context_summary(
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


def outline_generation_prompt(
    project: Project,
    world_snapshots: list[ProjectWorldSnapshot],
    character_snapshots: list[ProjectCharacterSnapshot],
    reference_draft: ReferenceStoryStructureDraft | None,
    user_requirements: str | None,
    story_outline_fields: tuple[str, ...],
    reference_draft_to_response,
) -> str:
    context = {
        "project": project_to_response(project),
        "world_snapshots": [world_snapshot_to_response(snapshot) for snapshot in world_snapshots],
        "character_snapshots": [character_snapshot_to_response(snapshot) for snapshot in character_snapshots],
        "reference_structure": reference_draft_to_response(reference_draft) if reference_draft else None,
        "user_requirements": user_requirements,
    }
    fields = ", ".join(story_outline_fields)
    return (
        "请根据以下项目上下文生成整体故事大纲。只返回 JSON 对象，不要返回 Markdown。\n"
        f"JSON 字段必须包含：{fields}。\n"
        "所有字段值使用中文字符串；没有内容时使用空字符串。\n\n"
        f"{json.dumps(context, ensure_ascii=False)}"
    )


def rewrite_prompt(project: Project, field: str, current_value: str, instruction: str) -> str:
    context = {
        "project": project_to_response(project),
        "field": field,
        "current_value": current_value,
        "instruction": instruction,
    }
    return (
        "请局部改写指定故事大纲字段。只返回 JSON 对象，不要返回 Markdown。\n"
        "JSON 字段必须包含 value，value 为改写后的中文字符串。\n\n"
        f"{json.dumps(context, ensure_ascii=False)}"
    )


def reference_extraction_prompt(project: Project, payload, retry_notes: str | None = None) -> str:
    context = {
        "project": project_to_response(project),
        "source_type": payload.source_type,
        "source_filename": payload.source_filename,
        "source_text": payload.source_text,
        "user_requirements": payload.user_requirements,
        "retry_notes": retry_notes,
    }
    fields = ", ".join(
        (
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
    )
    return (
        "请从参考故事中抽取可迁移叙事结构，并完成去具体化。只返回 JSON 对象，不要返回 Markdown。\n"
        f"JSON 字段必须包含：{fields}。\n"
        "不得出现原故事角色名、地名、组织名、专有名词、具体桥段、对白或原文句子；不要写摘要或改写。\n\n"
        f"{json.dumps(context, ensure_ascii=False)}"
    )
