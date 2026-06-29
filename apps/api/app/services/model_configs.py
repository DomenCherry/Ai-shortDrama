"""模型配置服务模块，封装模型配置存储、启用、软删除和外部接口测试逻辑。"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Optional
from uuid import uuid4

import httpx
from sqlalchemy import select, update

from app.core.db import get_session
from app.models.db_models import ModelApiConfig, ModelApiTestLog
from app.models.schemas import ModelApiConfigCreate, ModelApiConfigUpdate


IMAGE_PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "volcengine_seedream": {
        "provider_name": "火山方舟 Seedream",
        "api_base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "endpoint_path": "/images/generations",
        "supports_reference_image": True,
    }
}

VIDEO_PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "volcengine_seedance_1_5": {
        "provider_name": "火山方舟",
        "api_base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "endpoint_path": "/contents/generations/tasks",
    }
}

SEEDANCE_VIDEO_PRESET = "volcengine_seedance_1_5"
SEEDANCE_TEST_OPTIONS = {
    "resolution": "480p",
    "ratio": "16:9",
    "duration": 4,
    "generate_audio": False,
    "watermark": False,
    "camera_fixed": False,
    "draft": True,
}


def _now() -> datetime:
    """返回带 UTC 时区的当前时间，保证审计字段格式一致。"""
    return datetime.now(timezone.utc)


def _serialize_datetime(value: datetime | None) -> Optional[str]:
    """将可选时间转为 ISO 字符串，便于 API 响应序列化。"""
    return value.isoformat() if value else None


def _mask_api_key(api_key: str) -> str:
    """脱敏 API Key，避免密钥明文返回前端。"""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def _config_to_response(config: ModelApiConfig) -> dict[str, Any]:
    """序列化模型配置响应，并只返回脱敏后的密钥信息。"""
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
    """列出未软删除的模型配置，默认隐藏历史删除记录。"""
    with get_session() as session:
        configs = session.scalars(
            select(ModelApiConfig).where(ModelApiConfig.deleted_at.is_(None)).order_by(
                ModelApiConfig.config_type.asc(),
                ModelApiConfig.updated_at.desc(),
            )
        ).all()
        return [_config_to_response(config) for config in configs]


def get_config(config_id: str) -> dict[str, Any]:
    """读取单个未删除模型配置，删除后的配置对业务侧视为不存在。"""
    with get_session() as session:
        config = session.get(ModelApiConfig, config_id)
        if config is None or config.deleted_at is not None:
            raise ValueError("模型配置不存在")
        return _config_to_response(config)


def _validate_url(value: str | None) -> str:
    """校验 API 地址格式，避免把无效地址写入模型配置。"""
    if not value or not value.strip():
        raise ValueError("请填写 API 地址")
    normalized = value.strip().rstrip("/")
    if not normalized.startswith(("http://", "https://")) or " " in normalized:
        raise ValueError("API 地址必须以 http:// 或 https:// 开头，且不能包含空格")
    return normalized


def _generation_endpoint_path(value: str | None, default_path: str) -> str:
    """标准化生成接口路径，兼容用户是否填写前导斜杠。"""
    if not value:
        return default_path
    endpoint_path = value.strip()
    return endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"


def _default_endpoint_path(config_type: str) -> str | None:
    """返回需要单独配置 endpoint 的生成模型默认接口路径。"""
    if config_type == "image":
        return "/images/generations"
    if config_type == "video":
        return "/videos/generations"
    return None


def _resolve_provider_fields(payload: ModelApiConfigCreate) -> dict[str, Any]:
    """根据预设或自定义模式解析模型供应商字段。"""
    if payload.provider_mode == "preset":
        if payload.config_type == "image":
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

        if payload.config_type == "video":
            if not payload.provider_preset or payload.provider_preset not in VIDEO_PROVIDER_PRESETS:
                raise ValueError("该供应商预设暂不可用，请选择自定义配置")

            preset = VIDEO_PROVIDER_PRESETS[payload.provider_preset]
            return {
                "provider_mode": "preset",
                "provider_preset": payload.provider_preset,
                "provider_name": preset["provider_name"],
                "api_base_url": preset["api_base_url"],
                "endpoint_path": preset["endpoint_path"],
                "supports_reference_image": False,
            }

        raise ValueError("该供应商预设暂不可用，请选择自定义配置")

    if not payload.provider_name:
        raise ValueError("请填写供应商名称")

    default_endpoint_path = _default_endpoint_path(payload.config_type)

    return {
        "provider_mode": "custom",
        "provider_preset": None,
        "provider_name": payload.provider_name,
        "api_base_url": _validate_url(payload.api_base_url),
        "endpoint_path": _generation_endpoint_path(payload.endpoint_path, default_endpoint_path) if default_endpoint_path else None,
        "supports_reference_image": payload.supports_reference_image if payload.config_type == "image" else False,
    }


def create_config(payload: ModelApiConfigCreate) -> dict[str, Any]:
    """创建模型配置，并在启用时关闭同类型其他未删除配置。"""
    config_id = str(uuid4())
    now = _now()
    provider_fields = _resolve_provider_fields(payload)

    with get_session() as session:
        if payload.enabled:
            session.execute(
                update(ModelApiConfig)
                .where(ModelApiConfig.config_type == payload.config_type)
                .where(ModelApiConfig.deleted_at.is_(None))
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
            image_size=payload.image_size if payload.config_type == "image" else None,
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
    """读取指定类型当前启用的模型配置，供生成任务调用。"""
    with get_session() as session:
        config = session.scalars(
            select(ModelApiConfig)
            .where(ModelApiConfig.config_type == config_type)
            .where(ModelApiConfig.enabled.is_(True))
            .where(ModelApiConfig.deleted_at.is_(None))
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
    """测试模型配置连通性，并记录测试结果和失败原因。"""
    with get_session() as session:
        config = session.get(ModelApiConfig, config_id)
        if config is None or config.deleted_at is not None:
            raise ValueError("模型配置不存在")

        config_snapshot = {
            "id": config.id,
            "config_type": config.config_type,
            "api_base_url": config.api_base_url,
            "api_key_secret": config.api_key_secret,
            "model_name": config.model_name,
            "image_size": config.image_size,
            "endpoint_path": config.endpoint_path,
            "provider_mode": config.provider_mode,
            "provider_preset": config.provider_preset,
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
        elif config_snapshot["config_type"] == "image":
            response_summary = await _test_image_config(config_snapshot)
        elif config_snapshot["config_type"] == "video":
            response_summary = await _test_video_config(config_snapshot)
        else:
            raise ValueError("不支持的模型配置类型")
        success = True
        message = "接口测试成功"
    except httpx.HTTPStatusError as exc:
        message = _format_http_status_error(exc, config_snapshot)
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
        if config is None or config.deleted_at is not None:
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
    """调用文本模型测试接口，验证 API Key、地址和模型名可用。"""
    url = _text_chat_completions_url(config["api_base_url"])
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
    """调用图片模型测试接口，验证文生图配置可用。"""
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


async def _test_video_config(config: dict[str, Any]) -> str:
    """调用视频模型测试接口，验证文生视频配置可用。"""
    if config.get("provider_preset") == SEEDANCE_VIDEO_PRESET:
        return await _test_seedance_video_config(config)

    url = _join_api_url(config["api_base_url"], config.get("endpoint_path") or "/videos/generations")
    payload = {
        "model": config["model_name"],
        "prompt": "一个 2 秒的简单测试视频：现代城市街角，镜头缓慢推进。",
        "size": config["image_size"] or "1280x720",
        "duration": 2,
        "n": 1,
    }
    headers = {"Authorization": f"Bearer {config['api_key_secret']}"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    first_item = data.get("data", [{}])[0] if isinstance(data.get("data"), list) and data.get("data") else {}
    video_result = (
        first_item.get("url")
        or first_item.get("b64_json")
        or first_item.get("id")
        or data.get("id")
        or data.get("status")
    )
    if not video_result:
        raise ValueError("接口响应格式无法解析")
    return "video result received"


async def _test_seedance_video_config(config: dict[str, Any]) -> str:
    """按火山方舟 Seedance 视频生成任务接口创建异步测试任务。"""
    url = _join_api_url(config["api_base_url"], config.get("endpoint_path") or "/contents/generations/tasks")
    payload = {
        "model": config["model_name"],
        "content": [
            {
                "type": "text",
                "text": "接口连通性测试：现代城市街角，镜头缓慢推进，画面干净稳定。",
            }
        ],
        **SEEDANCE_TEST_OPTIONS,
    }
    headers = {"Authorization": f"Bearer {config['api_key_secret']}"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    task_id = data.get("id")
    if not task_id:
        raise ValueError("接口响应格式无法解析")
    return f"video task created: {task_id}"


def _format_http_status_error(exc: httpx.HTTPStatusError, config: dict[str, Any]) -> str:
    """将外部接口 HTTP 错误转换为可排查的信息，避免只显示状态码。"""
    status_code = exc.response.status_code
    message = f"接口返回错误状态：{status_code}"
    response_detail = _summarize_response_body(exc.response)
    if response_detail:
        message = f"{message}；响应：{response_detail}"

    if (
        status_code == 404
        and config.get("config_type") == "video"
        and config.get("provider_preset") == SEEDANCE_VIDEO_PRESET
    ):
        message = (
            f"{message}。请确认“模型名称”填写的是火山方舟控制台中已开通的 Seedance Model ID "
            "或推理接入点 Endpoint ID，并且 API Key 属于同一地域/账号。"
        )
    return message[:600]


def _summarize_response_body(response: httpx.Response) -> str:
    """提取外部接口响应体中的关键错误信息，并限制长度。"""
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        return text[:300]

    if not isinstance(data, dict):
        return json.dumps(data, ensure_ascii=False)[:300]

    candidates: list[str] = []
    for key in ("message", "msg", "error", "code"):
        value = data.get(key)
        if isinstance(value, str) and value:
            candidates.append(f"{key}={value}")
        elif isinstance(value, dict):
            nested = value.get("message") or value.get("code") or value.get("type")
            if nested:
                candidates.append(f"{key}={nested}")

    if not candidates:
        candidates.append(json.dumps(data, ensure_ascii=False))
    return "；".join(candidates)[:300]


def _join_api_url(api_base_url: str, endpoint_path: str) -> str:
    """拼接 API 基础地址和接口路径，避免重复或缺失斜杠。"""
    return f"{api_base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"


def _text_chat_completions_url(api_base_url: str) -> str:
    """生成 OpenAI 兼容 chat completions 地址。"""
    normalized_base_url = api_base_url.rstrip("/")
    # 文本模型配置约定填写 Base URL，但兼容用户误填完整 chat completions 路径，避免重复拼接导致 404。
    if normalized_base_url.endswith("/chat/completions"):
        return normalized_base_url
    return f"{normalized_base_url}/chat/completions"


def update_config(config_id: str, payload: ModelApiConfigUpdate) -> dict[str, Any]:
    """更新未删除模型配置，必要时同步处理启用状态。"""
    with get_session() as session:
        config = session.get(ModelApiConfig, config_id)
        if config is None or config.deleted_at is not None:
            raise ValueError("模型配置不存在")

        provider_fields = _resolve_provider_fields_for_update(config.config_type, payload)

        if payload.enabled is True:
            session.execute(
                update(ModelApiConfig)
                .where(ModelApiConfig.config_type == config.config_type)
                .where(ModelApiConfig.id != config_id)
                .where(ModelApiConfig.deleted_at.is_(None))
                .values(enabled=False)
            )

        config.provider_mode = provider_fields["provider_mode"]
        config.provider_preset = provider_fields["provider_preset"]
        config.provider_name = provider_fields["provider_name"]
        config.api_base_url = provider_fields["api_base_url"]
        if payload.api_key:
            config.api_key_secret = payload.api_key
        config.model_name = payload.model_name
        config.image_size = payload.image_size if config.config_type == "image" else None
        config.endpoint_path = provider_fields["endpoint_path"]
        config.supports_reference_image = provider_fields["supports_reference_image"]
        config.remark = payload.remark
        if payload.enabled is not None:
            config.enabled = payload.enabled
        config.last_test_status = "untested"
        config.updated_at = _now()

        session.flush()
        return _config_to_response(config)


def _resolve_provider_fields_for_update(config_type: str, payload: ModelApiConfigUpdate) -> dict[str, Any]:
    """更新配置时解析供应商字段，并保护预设配置的固定接口参数。"""
    if payload.provider_mode == "preset":
        if config_type == "image":
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

        if config_type == "video":
            if not payload.provider_preset or payload.provider_preset not in VIDEO_PROVIDER_PRESETS:
                raise ValueError("该供应商预设暂不可用，请选择自定义配置")

            preset = VIDEO_PROVIDER_PRESETS[payload.provider_preset]
            return {
                "provider_mode": "preset",
                "provider_preset": payload.provider_preset,
                "provider_name": preset["provider_name"],
                "api_base_url": preset["api_base_url"],
                "endpoint_path": preset["endpoint_path"],
                "supports_reference_image": False,
            }

        raise ValueError("该供应商预设暂不可用，请选择自定义配置")

    if not payload.provider_name:
        raise ValueError("请填写供应商名称")

    default_endpoint_path = _default_endpoint_path(config_type)

    return {
        "provider_mode": "custom",
        "provider_preset": None,
        "provider_name": payload.provider_name,
        "api_base_url": _validate_url(payload.api_base_url),
        "endpoint_path": _generation_endpoint_path(payload.endpoint_path, default_endpoint_path) if default_endpoint_path else None,
        "supports_reference_image": payload.supports_reference_image if config_type == "image" else False,
    }


def delete_config(config_id: str) -> None:
    """软删除模型配置，保留测试日志和历史排查信息。"""
    with get_session() as session:
        config = session.get(ModelApiConfig, config_id)
        if config is None or config.deleted_at is not None:
            raise ValueError("模型配置不存在")

        now = _now()
        # 软删除配置，避免破坏 model_api_test_logs 的外键引用，同时让配置不再参与生成任务。
        config.enabled = False
        config.deleted_at = now
        config.updated_at = now


def enable_config(config_id: str) -> dict[str, Any]:
    """启用指定模型配置，并关闭同类型其他未删除配置。"""
    with get_session() as session:
        config = session.get(ModelApiConfig, config_id)
        if config is None or config.deleted_at is not None:
            raise ValueError("模型配置不存在")

        session.execute(
            update(ModelApiConfig)
            .where(ModelApiConfig.config_type == config.config_type)
            .where(ModelApiConfig.id != config_id)
            .where(ModelApiConfig.deleted_at.is_(None))
            .values(enabled=False)
        )

        config.enabled = True
        config.updated_at = _now()
        session.flush()
        return _config_to_response(config)
