from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Optional
from uuid import uuid4

import httpx
from sqlalchemy import select, update

from app.core.db import get_session
from app.models.db_models import ModelApiConfig, ModelApiTestLog
from app.models.schemas import ModelApiConfigCreate


IMAGE_PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "volcengine_seedream": {
        "provider_name": "火山方舟 Seedream",
        "api_base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "endpoint_path": "/images/generations",
        "supports_reference_image": True,
    }
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_datetime(value: datetime | None) -> Optional[str]:
    return value.isoformat() if value else None


def _mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def _config_to_response(config: ModelApiConfig) -> dict[str, Any]:
    return {
        "id": config.id,
        "config_type": config.config_type,
        "provider_mode": config.provider_mode,
        "provider_preset": config.provider_preset,
        "provider_name": config.provider_name,
        "api_base_url": config.api_base_url,
        "api_key_masked": _mask_api_key(config.api_key_secret),
        "model_name": config.model_name,
        "image_size": config.image_size,
        "endpoint_path": config.endpoint_path,
        "supports_reference_image": config.supports_reference_image,
        "remark": config.remark,
        "enabled": config.enabled,
        "last_test_status": config.last_test_status,
        "last_tested_at": _serialize_datetime(config.last_tested_at),
        "last_test_error": config.last_test_error,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
    }


def list_configs() -> list[dict[str, Any]]:
    with get_session() as session:
        configs = session.scalars(
            select(ModelApiConfig).order_by(
                ModelApiConfig.config_type.asc(),
                ModelApiConfig.updated_at.desc(),
            )
        ).all()
        return [_config_to_response(config) for config in configs]


def _validate_url(value: str | None) -> str:
    if not value or not value.strip():
        raise ValueError("请填写 API 地址")
    normalized = value.strip().rstrip("/")
    if not normalized.startswith(("http://", "https://")) or " " in normalized:
        raise ValueError("API 地址必须以 http:// 或 https:// 开头，且不能包含空格")
    return normalized


def _image_endpoint_path(value: str | None) -> str:
    if not value:
        return "/images/generations"
    endpoint_path = value.strip()
    return endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"


def _resolve_provider_fields(payload: ModelApiConfigCreate) -> dict[str, Any]:
    if payload.provider_mode == "preset":
        if payload.config_type != "image":
            raise ValueError("供应商预设目前仅用于图片模型配置")
        if not payload.provider_preset or payload.provider_preset not in IMAGE_PROVIDER_PRESETS:
            raise ValueError("该供应商预设暂不可用，请选择自定义配置")

        preset = IMAGE_PROVIDER_PRESETS[payload.provider_preset]
        return {
            "provider_mode": "preset",
            "provider_preset": payload.provider_preset,
            "provider_name": preset["provider_name"],
            "api_base_url": preset["api_base_url"],
            "endpoint_path": preset["endpoint_path"],
            "supports_reference_image": preset["supports_reference_image"],
        }

    if not payload.provider_name:
        raise ValueError("请填写供应商名称")

    return {
        "provider_mode": "custom",
        "provider_preset": None,
        "provider_name": payload.provider_name,
        "api_base_url": _validate_url(payload.api_base_url),
        "endpoint_path": _image_endpoint_path(payload.endpoint_path) if payload.config_type == "image" else None,
        "supports_reference_image": payload.supports_reference_image if payload.config_type == "image" else False,
    }


def create_config(payload: ModelApiConfigCreate) -> dict[str, Any]:
    config_id = str(uuid4())
    now = _now()
    provider_fields = _resolve_provider_fields(payload)

    with get_session() as session:
        if payload.enabled:
            session.execute(
                update(ModelApiConfig)
                .where(ModelApiConfig.config_type == payload.config_type)
                .values(enabled=False)
            )

        config = ModelApiConfig(
            id=config_id,
            config_type=payload.config_type,
            provider_mode=provider_fields["provider_mode"],
            provider_preset=provider_fields["provider_preset"],
            provider_name=provider_fields["provider_name"],
            api_base_url=provider_fields["api_base_url"],
            api_key_secret=payload.api_key,
            model_name=payload.model_name,
            image_size=payload.image_size,
            endpoint_path=provider_fields["endpoint_path"],
            supports_reference_image=provider_fields["supports_reference_image"],
            remark=payload.remark,
            enabled=payload.enabled,
            last_test_status="untested",
            created_at=now,
            updated_at=now,
        )
        session.add(config)
        session.flush()
        return _config_to_response(config)


def get_enabled_config(config_type: str) -> Optional[dict[str, Any]]:
    with get_session() as session:
        config = session.scalars(
            select(ModelApiConfig)
            .where(ModelApiConfig.config_type == config_type)
            .where(ModelApiConfig.enabled.is_(True))
            .order_by(ModelApiConfig.updated_at.desc())
            .limit(1)
        ).first()

        if config is None:
            return None

        return {
            "id": config.id,
            "config_type": config.config_type,
            "provider_mode": config.provider_mode,
            "provider_preset": config.provider_preset,
            "provider_name": config.provider_name,
            "api_base_url": config.api_base_url,
            "api_key_secret": config.api_key_secret,
            "model_name": config.model_name,
            "image_size": config.image_size,
            "endpoint_path": config.endpoint_path,
            "supports_reference_image": config.supports_reference_image,
            "last_test_status": config.last_test_status,
        }


async def test_config(config_id: str) -> dict[str, Any]:
    with get_session() as session:
        config = session.get(ModelApiConfig, config_id)
        if config is None:
            raise ValueError("模型配置不存在")

        config_snapshot = {
            "id": config.id,
            "config_type": config.config_type,
            "api_base_url": config.api_base_url,
            "api_key_secret": config.api_key_secret,
            "model_name": config.model_name,
            "image_size": config.image_size,
            "endpoint_path": config.endpoint_path,
            "supports_reference_image": config.supports_reference_image,
        }

    start = perf_counter()
    tested_at = _now()
    success = False
    message = ""
    response_summary = None

    try:
        if config_snapshot["config_type"] == "text":
            response_summary = await _test_text_config(config_snapshot)
        else:
            response_summary = await _test_image_config(config_snapshot)
        success = True
        message = "接口测试成功"
    except httpx.HTTPStatusError as exc:
        message = f"接口返回错误状态：{exc.response.status_code}"
    except httpx.RequestError:
        message = "接口无法访问，请检查 API 地址或网络连接"
    except ValueError as exc:
        message = str(exc)
    except Exception:
        message = "接口测试失败，请检查配置"

    latency_ms = int((perf_counter() - start) * 1000)
    status = "success" if success else "failed"

    with get_session() as session:
        config = session.get(ModelApiConfig, config_id)
        if config is None:
            raise ValueError("模型配置不存在")

        config.last_test_status = status
        config.last_tested_at = tested_at
        config.last_test_error = None if success else message
        config.updated_at = tested_at

        session.add(
            ModelApiTestLog(
                id=str(uuid4()),
                config_id=config_id,
                config_type=config_snapshot["config_type"],
                request_summary="connectivity test",
                success=success,
                response_summary=response_summary,
                error_message=None if success else message,
                latency_ms=latency_ms,
                tested_at=tested_at,
            )
        )

    return {
        "success": success,
        "status": status,
        "message": message,
        "latency_ms": latency_ms,
        "tested_at": tested_at.isoformat(),
    }


async def _test_text_config(config: dict[str, Any]) -> str:
    url = f"{config['api_base_url'].rstrip('/')}/chat/completions"
    payload = {
        "model": config["model_name"],
        "messages": [{"role": "user", "content": "请返回一句中文短句：接口可用。"}],
        "max_tokens": 20,
    }
    headers = {"Authorization": f"Bearer {config['api_key_secret']}"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    text = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    if not text:
        raise ValueError("接口响应格式无法解析")
    return text[:120]


async def _test_image_config(config: dict[str, Any]) -> str:
    url = _join_api_url(config["api_base_url"], config.get("endpoint_path") or "/images/generations")
    payload = {
        "model": config["model_name"],
        "prompt": "一张简单的角色头像示意图，现代都市风格，干净背景。",
        "size": config["image_size"] or "1024x1024",
        "n": 1,
    }
    headers = {"Authorization": f"Bearer {config['api_key_secret']}"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    image_result = data.get("data", [{}])[0].get("url") or data.get("data", [{}])[0].get("b64_json")
    if not image_result:
        raise ValueError("接口响应格式无法解析")
    return "image result received"


def _join_api_url(api_base_url: str, endpoint_path: str) -> str:
    return f"{api_base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
