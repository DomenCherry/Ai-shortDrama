from __future__ import annotations

import base64
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import httpx
from sqlalchemy import or_, select

from app.core.config import get_settings
from app.core.db import get_session
from app.models.db_models import CharacterCard, Project, ProjectCharacterSnapshot
from app.models.schemas import (
    CharacterCardCreate,
    CharacterCardUpdate,
    CharacterReferenceImageUpload,
    CharacterTurnaroundGenerate,
    ProjectCharacterSnapshotCreate,
)
from app.services import model_configs


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _character_card_to_response(card: CharacterCard) -> dict[str, Any]:
    return {
        "id": card.id,
        "name": card.name,
        "gender": card.gender,
        "role_type": card.role_type,
        "identity": card.identity,
        "background": card.background,
        "personality": card.personality,
        "goal": card.goal,
        "motivation": card.motivation,
        "secret": card.secret,
        "conflict_points": card.conflict_points,
        "relationship_notes": card.relationship_notes,
        "speech_style": card.speech_style,
        "catchphrases": card.catchphrases,
        "emotional_arc": card.emotional_arc,
        "story_function": card.story_function,
        "visual_description": card.visual_description,
        "image_keywords": card.image_keywords,
        "reference_image_url": card.reference_image_url,
        "reference_local_path": card.reference_local_path,
        "turnaround_prompt": card.turnaround_prompt,
        "turnaround_image_url": card.turnaround_image_url,
        "turnaround_local_path": card.turnaround_local_path,
        "turnaround_generation_prompt": card.turnaround_generation_prompt,
        "turnaround_status": card.turnaround_status,
        "turnaround_version": card.turnaround_version,
        "turnaround_confirmed_at": card.turnaround_confirmed_at.isoformat() if card.turnaround_confirmed_at else None,
        "version": card.version,
        "status": card.status,
        "created_at": card.created_at.isoformat(),
        "updated_at": card.updated_at.isoformat(),
    }


def _snapshot_to_response(snapshot: ProjectCharacterSnapshot) -> dict[str, Any]:
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


def _payload_to_card_fields(payload: CharacterCardCreate | CharacterCardUpdate) -> dict[str, Any]:
    return {
        "name": payload.name,
        "gender": payload.gender,
        "role_type": payload.role_type,
        "identity": payload.identity,
        "background": payload.background,
        "personality": payload.personality,
        "goal": payload.goal,
        "motivation": payload.motivation,
        "secret": payload.secret,
        "conflict_points": payload.conflict_points,
        "relationship_notes": payload.relationship_notes,
        "speech_style": payload.speech_style,
        "catchphrases": payload.catchphrases,
        "emotional_arc": payload.emotional_arc,
        "story_function": payload.story_function,
        "visual_description": payload.visual_description,
        "image_keywords": payload.image_keywords,
        "reference_image_url": payload.reference_image_url,
        "reference_local_path": payload.reference_local_path,
        "turnaround_prompt": payload.turnaround_prompt,
        "status": payload.status,
    }


def _asset_root() -> Path:
    return Path(get_settings().asset_root)


def _public_asset_url(local_path: Path) -> str:
    relative_path = local_path.relative_to(_asset_root()).as_posix()
    return f"/api/assets/{relative_path}"


def _character_asset_dir(card_id: str) -> Path:
    directory = _asset_root() / "character-cards" / card_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _decode_data_url(data_url: str) -> bytes:
    if "," not in data_url:
        raise ValueError("图片数据格式不正确")
    header, encoded = data_url.split(",", 1)
    if ";base64" not in header:
        raise ValueError("图片数据必须是 base64 格式")
    return base64.b64decode(encoded)


def _image_extension(content_type: str, filename: str) -> str:
    allowed_types = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
    }
    if content_type not in allowed_types:
        raise ValueError("请上传 png、jpg 或 webp 格式图片")
    suffix = Path(filename).suffix.lower()
    return suffix if suffix in {".png", ".jpg", ".jpeg", ".webp"} else allowed_types[content_type]


def _turnaround_prompt(card: CharacterCard, override_prompt: str | None = None) -> str:
    parts = [
        "请生成同一角色的人物三视图，画面包含正面、侧面、背面，全身，统一服装，干净背景。",
        "输出应适合作为短剧人物视觉参考，不模仿任何特定现实人物。",
        f"角色名：{card.name}",
        f"性别：{card.gender}",
        f"角色类型：{card.role_type}",
        f"身份摘要：{card.identity}",
        f"人物目标：{card.goal}",
    ]
    optional_fields = [
        ("人物背景", card.background),
        ("性格", card.personality),
        ("深层动机", card.motivation),
        ("人物秘密", card.secret),
        ("冲突点", card.conflict_points),
        ("人物关系", card.relationship_notes),
        ("说话方式", card.speech_style),
        ("常用表达", card.catchphrases),
        ("情感弧线", card.emotional_arc),
        ("剧情功能", card.story_function),
        ("视觉描述", card.visual_description),
        ("形象关键词", card.image_keywords),
        ("用户三视图提示词", override_prompt or card.turnaround_prompt),
    ]
    parts.extend(f"{label}：{value}" for label, value in optional_fields if value)
    if card.reference_image_url:
        parts.append(f"参考图：{card.reference_image_url}")
    return "\n".join(parts)


def _reference_image_data_url(card: CharacterCard) -> str | None:
    if not card.reference_local_path:
        return None

    local_path = Path(card.reference_local_path)
    if not local_path.exists() or not local_path.is_file():
        raise ValueError("角色参考图文件不存在，请重新上传参考图")

    content_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    content_type = content_types.get(local_path.suffix.lower())
    if not content_type:
        raise ValueError("角色参考图格式不支持，请重新上传 png、jpg 或 webp 图片")

    # 参考图以 data URL 传入图片模型，避免暴露本地文件系统路径给外部服务。
    encoded = base64.b64encode(local_path.read_bytes()).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def _turnaround_to_response(card: CharacterCard) -> dict[str, Any]:
    return {
        "character_card_id": card.id,
        "image_url": card.turnaround_image_url,
        "local_path": card.turnaround_local_path,
        "generation_prompt": card.turnaround_generation_prompt,
        "status": card.turnaround_status,
        "version": card.turnaround_version,
        "confirmed_at": card.turnaround_confirmed_at.isoformat() if card.turnaround_confirmed_at else None,
        "updated_at": card.updated_at.isoformat(),
    }


def list_character_cards(
    search: Optional[str] = None,
    gender: Optional[str] = None,
    role_type: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    with get_session() as session:
        statement = select(CharacterCard)
        if search:
            keyword = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    CharacterCard.name.ilike(keyword),
                    CharacterCard.identity.ilike(keyword),
                )
            )
        if gender:
            statement = statement.where(CharacterCard.gender == gender)
        if role_type:
            statement = statement.where(CharacterCard.role_type == role_type)
        if status:
            statement = statement.where(CharacterCard.status == status)

        cards = session.scalars(statement.order_by(CharacterCard.updated_at.desc())).all()
        return [_character_card_to_response(card) for card in cards]


def create_character_card(payload: CharacterCardCreate) -> dict[str, Any]:
    now = _now()
    card = CharacterCard(
        id=str(uuid4()),
        **_payload_to_card_fields(payload),
        version=1,
        turnaround_status="none",
        turnaround_version=0,
        created_at=now,
        updated_at=now,
    )

    with get_session() as session:
        session.add(card)
        session.flush()
        return _character_card_to_response(card)


def get_character_card(card_id: str) -> dict[str, Any]:
    with get_session() as session:
        card = session.get(CharacterCard, card_id)
        if not card:
            raise ValueError("角色卡不存在")
        return _character_card_to_response(card)


def update_character_card(card_id: str, payload: CharacterCardUpdate) -> dict[str, Any]:
    with get_session() as session:
        card = session.get(CharacterCard, card_id)
        if not card:
            raise ValueError("角色卡不存在")

        fields = _payload_to_card_fields(payload)
        has_content_change = any(getattr(card, key) != value for key, value in fields.items())
        for key, value in fields.items():
            setattr(card, key, value)

        # 角色核心内容变化后提升版本，项目快照可据此判断是否落后于来源角色卡。
        if has_content_change:
            card.version += 1
        card.updated_at = _now()
        session.flush()
        return _character_card_to_response(card)


def archive_character_card(card_id: str) -> dict[str, Any]:
    with get_session() as session:
        card = session.get(CharacterCard, card_id)
        if not card:
            raise ValueError("角色卡不存在")

        # 使用归档替代硬删除，避免破坏历史项目中已加载快照的来源追踪。
        if card.status != "archived":
            card.status = "archived"
            card.version += 1
            card.updated_at = _now()
        session.flush()
        return _character_card_to_response(card)


def activate_character_card(card_id: str) -> dict[str, Any]:
    with get_session() as session:
        card = session.get(CharacterCard, card_id)
        if not card:
            raise ValueError("角色卡不存在")

        if card.status != "active":
            card.status = "active"
            card.version += 1
            card.updated_at = _now()
        session.flush()
        return _character_card_to_response(card)


def load_character_card_to_project(project_id: str, payload: ProjectCharacterSnapshotCreate) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        card = session.get(CharacterCard, payload.source_character_card_id)
        if not card:
            raise ValueError("角色卡不存在")
        if card.status != "active":
            raise ValueError("只有可加载状态的角色卡可以加入项目")

        now = _now()
        snapshot_content = json.dumps(_character_card_to_response(card), ensure_ascii=False)

        if payload.load_mode == "replace":
            if not payload.replace_snapshot_id:
                raise ValueError("替换角色时必须提供项目内角色快照 ID")
            snapshot = session.get(ProjectCharacterSnapshot, payload.replace_snapshot_id)
            if not snapshot or snapshot.project_id != project_id:
                raise ValueError("要替换的项目角色不存在")

            # 替换只更新当前项目快照，不回写角色卡库原始内容，也不影响其他项目。
            snapshot.source_character_card_id = card.id
            snapshot.source_version = card.version
            snapshot.name = card.name
            snapshot.gender = card.gender
            snapshot.role_type = card.role_type
            snapshot.snapshot_content = snapshot_content
            snapshot.visual_description = card.visual_description
            snapshot.reference_image_url = card.reference_image_url
            snapshot.reference_local_path = card.reference_local_path
            snapshot.updated_at = now
        else:
            existing_snapshot = session.scalar(
                select(ProjectCharacterSnapshot).where(
                    ProjectCharacterSnapshot.project_id == project_id,
                    ProjectCharacterSnapshot.name == card.name,
                )
            )
            # 同名角色需要用户明确选择替换，避免加载时静默覆盖或制造难以区分的项目角色。
            if existing_snapshot:
                raise ValueError("角色名与项目中已有角色重复，请选择替换已有角色或修改角色名")

            # 加载角色卡时复制为项目内快照，保证项目后续创作上下文稳定。
            snapshot = ProjectCharacterSnapshot(
                id=str(uuid4()),
                project_id=project_id,
                source_character_card_id=card.id,
                source_version=card.version,
                name=card.name,
                gender=card.gender,
                role_type=card.role_type,
                snapshot_content=snapshot_content,
                visual_description=card.visual_description,
                reference_image_url=card.reference_image_url,
                reference_local_path=card.reference_local_path,
                loaded_at=now,
                updated_at=now,
            )
            session.add(snapshot)

        session.flush()
        return _snapshot_to_response(snapshot)


def upload_reference_image(card_id: str, payload: CharacterReferenceImageUpload) -> dict[str, Any]:
    image_bytes = _decode_data_url(payload.data_url)
    if len(image_bytes) > 10 * 1024 * 1024:
        raise ValueError("参考图不能超过 10MB")

    with get_session() as session:
        card = session.get(CharacterCard, card_id)
        if not card:
            raise ValueError("角色卡不存在")

        extension = _image_extension(payload.content_type, payload.filename)
        local_path = _character_asset_dir(card_id) / f"reference-{uuid4().hex}{extension}"
        local_path.write_bytes(image_bytes)

        # 参考图作为三视图生成的输入素材保存；用户不再需要手工填写本地路径。
        card.reference_local_path = str(local_path)
        card.reference_image_url = _public_asset_url(local_path)
        card.updated_at = _now()
        session.flush()

        return {
            "character_card_id": card.id,
            "image_url": card.reference_image_url,
            "local_path": card.reference_local_path,
            "updated_at": card.updated_at.isoformat(),
        }


async def generate_turnaround_image(card_id: str, payload: CharacterTurnaroundGenerate) -> dict[str, Any]:
    with get_session() as session:
        card = session.get(CharacterCard, card_id)
        if not card:
            raise ValueError("角色卡不存在")
        prompt = _turnaround_prompt(card, payload.prompt)
        reference_image_data_url = _reference_image_data_url(card)

    image_config = model_configs.get_enabled_config("image")
    if not image_config or image_config["last_test_status"] != "success":
        raise ValueError("请先在模型设置中配置可用的图片生成 API")
    if reference_image_data_url and not image_config.get("supports_reference_image"):
        raise ValueError("当前图片模型不支持参考图输入，请更换模型或关闭参考图能力")

    try:
        generated_image = await _call_image_generation_api(image_config, prompt, reference_image_data_url)
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"图片生成接口返回错误状态：{exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise ValueError("图片生成接口无法访问，请检查 API 地址或网络连接") from exc

    with get_session() as session:
        card = session.get(CharacterCard, card_id)
        if not card:
            raise ValueError("角色卡不存在")

        if generated_image["kind"] == "b64_json":
            local_path = _character_asset_dir(card_id) / f"turnaround-v{card.turnaround_version + 1}-{uuid4().hex}.png"
            local_path.write_bytes(base64.b64decode(generated_image["value"]))
            image_url = _public_asset_url(local_path)
            local_path_value = str(local_path)
        else:
            image_url = generated_image["value"]
            local_path_value = None

        # 三视图生成结果先作为候选图保存，必须经用户确认后才进入后续视频参考素材。
        card.turnaround_prompt = payload.prompt or card.turnaround_prompt
        card.turnaround_image_url = image_url
        card.turnaround_local_path = local_path_value
        card.turnaround_generation_prompt = prompt
        card.turnaround_status = "generated"
        card.turnaround_version += 1
        card.turnaround_confirmed_at = None
        card.updated_at = _now()
        session.flush()
        return _turnaround_to_response(card)


def confirm_turnaround_image(card_id: str, image_id: str | None = None) -> dict[str, Any]:
    with get_session() as session:
        card = session.get(CharacterCard, card_id)
        if not card:
            raise ValueError("角色卡不存在")
        if not card.turnaround_image_url:
            raise ValueError("请先生成人物三视图")
        if image_id and image_id != str(card.turnaround_version):
            raise ValueError("三视图版本不存在或已不是当前候选图")

        card.turnaround_status = "confirmed"
        card.turnaround_confirmed_at = _now()
        card.updated_at = card.turnaround_confirmed_at
        session.flush()
        return _turnaround_to_response(card)


async def _call_image_generation_api(
    config: dict[str, Any],
    prompt: str,
    reference_image_data_url: str | None = None,
) -> dict[str, str]:
    url = _join_api_url(config["api_base_url"], config.get("endpoint_path") or "/images/generations")
    payload = {
        "model": config["model_name"],
        "prompt": prompt,
        "size": config["image_size"] or "1024x1024",
        "n": 1,
    }
    if reference_image_data_url:
        # 火山方舟 Seedream 等图像模型使用 image 字段接收参考图；自定义供应商需自行确认兼容性。
        payload["image"] = [reference_image_data_url]
    headers = {"Authorization": f"Bearer {config['api_key_secret']}"}
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    image_data = data.get("data", [{}])[0]
    if image_data.get("b64_json"):
        return {"kind": "b64_json", "value": image_data["b64_json"]}
    if image_data.get("url"):
        return {"kind": "url", "value": image_data["url"]}
    raise ValueError("图片生成接口响应格式无法解析")


def _join_api_url(api_base_url: str, endpoint_path: str) -> str:
    return f"{api_base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
