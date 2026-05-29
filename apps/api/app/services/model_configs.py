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
        "provider_name": config.provider_name,
        "api_base_url": config.api_base_url,
        "api_key_masked": _mask_api_key(config.api_key_secret),
        "model_name": config.model_name,
        "image_size": config.image_size,
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


def create_config(payload: ModelApiConfigCreate) -> dict[str, Any]:
    config_id = str(uuid4())
    now = _now()

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
            provider_name=payload.provider_name,
            api_base_url=str(payload.api_base_url).rstrip("/"),
            api_key_secret=payload.api_key,
            model_name=payload.model_name,
            image_size=payload.image_size,
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
            "provider_name": config.provider_name,
            "api_base_url": config.api_base_url,
            "api_key_secret": config.api_key_secret,
            "model_name": config.model_name,
            "image_size": config.image_size,
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
    url = f"{config['api_base_url'].rstrip('/')}/images/generations"
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
