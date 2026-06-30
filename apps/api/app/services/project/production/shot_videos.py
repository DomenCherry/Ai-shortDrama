"""镜头级文生视频任务提交、状态刷新和结果采用。"""
from __future__ import annotations

import json
from time import perf_counter
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import select, update

from app.core.db import get_session
from app.models.db_models import (
    ModelApiConfig,
    Project,
    ProjectShotPrompt,
    ProjectShotVideoGeneration,
    ProjectStoryboardShot,
)
from app.services import model_configs
from app.services.model_configs import SEEDANCE_VIDEO_PRESET
from app.services.project.common import now_utc, validate_episode_no


ACTIVE_STATUSES = {"queued", "running"}


def _loads(value: str | None, fallback):
    try:
        return json.loads(value) if value else fallback
    except (json.JSONDecodeError, TypeError):
        return fallback


def _join_api_url(api_base_url: str, endpoint_path: str) -> str:
    return f"{api_base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"


def _serialize_generation(
    generation: ProjectShotVideoGeneration,
    current_shot_revision: int | None = None,
    current_prompt_revision: int | None = None,
) -> dict[str, Any]:
    is_stale = False
    if current_shot_revision is not None and generation.source_shot_revision != current_shot_revision:
        is_stale = True
    if (
        current_prompt_revision is not None
        and generation.source_prompt_revision is not None
        and generation.source_prompt_revision != current_prompt_revision
    ):
        is_stale = True
    return {
        "id": generation.id,
        "project_id": generation.project_id,
        "episode_no": generation.episode_no,
        "storyboard_id": generation.storyboard_id,
        "shot_id": generation.shot_id,
        "prompt_id": generation.prompt_id,
        "source_shot_revision": generation.source_shot_revision,
        "source_prompt_revision": generation.source_prompt_revision,
        "video_prompt_snapshot": generation.video_prompt_snapshot,
        "negative_prompt_snapshot": generation.negative_prompt_snapshot,
        "reference_asset_ids": _loads(generation.reference_asset_ids, []),
        "model_config_id": generation.model_config_id,
        "model_name": generation.model_name,
        "provider_preset": generation.provider_preset,
        "provider_task_id": generation.provider_task_id,
        "status": generation.status,
        "result_url": generation.result_url,
        "local_asset_path": generation.local_asset_path,
        "thumbnail_url": generation.thumbnail_url,
        "duration_seconds": generation.duration_seconds,
        "width": generation.width,
        "height": generation.height,
        "error_message": generation.error_message,
        "request_payload_snapshot": _loads(generation.request_payload_snapshot, {}),
        "elapsed_ms": generation.elapsed_ms,
        "adopted": generation.adopted,
        "adopted_at": generation.adopted_at.isoformat() if generation.adopted_at else None,
        "is_stale": is_stale,
        "created_at": generation.created_at.isoformat(),
        "updated_at": generation.updated_at.isoformat(),
    }


def _shot_and_prompt(session, project_id: str, episode_no: int, shot_id: str) -> tuple[ProjectStoryboardShot, ProjectShotPrompt | None]:
    project = session.get(Project, project_id)
    if not project:
        raise ValueError("项目不存在")
    validate_episode_no(project, episode_no)
    shot = session.get(ProjectStoryboardShot, shot_id)
    if not shot or shot.project_id != project_id or shot.episode_no != episode_no or not shot.storyboard_id:
        raise ValueError("项目分镜不存在")
    prompt = session.scalars(select(ProjectShotPrompt).where(ProjectShotPrompt.shot_id == shot_id)).first()
    return shot, prompt


def _generation_for_shot(session, project_id: str, episode_no: int, shot_id: str, generation_id: str) -> ProjectShotVideoGeneration:
    _shot_and_prompt(session, project_id, episode_no, shot_id)
    generation = session.get(ProjectShotVideoGeneration, generation_id)
    if not generation or generation.project_id != project_id or generation.episode_no != episode_no or generation.shot_id != shot_id:
        raise ValueError("视频生成记录不存在")
    return generation


def _enabled_video_config() -> dict[str, Any]:
    config = model_configs.get_enabled_config("video")
    if not config:
        raise ValueError("请先配置视频生成模型 API")
    if config["last_test_status"] != "success":
        raise ValueError("请先测试并通过当前视频生成模型 API")
    return config


def _video_config_by_id(config_id: str) -> dict[str, Any]:
    with get_session() as session:
        config = session.get(ModelApiConfig, config_id)
        if not config or config.deleted_at is not None:
            raise ValueError("视频模型配置不存在，无法刷新任务")
        return {
            "id": config.id,
            "api_base_url": config.api_base_url,
            "api_key_secret": config.api_key_secret,
            "model_name": config.model_name,
            "image_size": config.image_size,
            "endpoint_path": config.endpoint_path,
            "provider_preset": config.provider_preset,
        }


def _prompt_text(prompt: ProjectShotPrompt | None) -> str:
    if not prompt:
        raise ValueError("请先填写视频提示词")
    text = (prompt.seedance_prompt or prompt.video_prompt or "").strip()
    if not text:
        raise ValueError("请先填写视频提示词")
    if prompt.freshness == "needs_update":
        raise ValueError("提示词需要更新，请先保存或确认后再生成视频")
    return text


def _request_payload(config: dict[str, Any], shot: ProjectStoryboardShot, prompt: ProjectShotPrompt | None, prompt_text: str) -> dict[str, Any]:
    negative = (prompt.negative_prompt or "").strip() if prompt else ""
    text = f"{prompt_text}\n负面提示：{negative}" if negative else prompt_text
    if config.get("provider_preset") == SEEDANCE_VIDEO_PRESET:
        return {
            "model": config["model_name"],
            "content": [{"type": "text", "text": text}],
            "resolution": "720p",
            "ratio": prompt.aspect_ratio if prompt and prompt.aspect_ratio else "16:9",
            "duration": max(1, int(round(shot.duration_seconds or 4))),
            "generate_audio": False,
            "watermark": False,
            "camera_fixed": False,
        }
    return {
        "model": config["model_name"],
        "prompt": text,
        "size": config.get("image_size") or "1280x720",
        "duration": max(1, int(round(shot.duration_seconds or 4))),
        "n": 1,
    }


def _status_from_response(data: dict[str, Any]) -> str:
    raw = str(data.get("status") or data.get("task_status") or data.get("state") or "").lower()
    if raw in {"succeeded", "success", "completed", "complete", "done", "finished"}:
        return "succeeded"
    if raw in {"failed", "fail", "error", "canceled", "cancelled"}:
        return "canceled" if raw in {"canceled", "cancelled"} else "failed"
    return "running"


def _first_item(data: dict[str, Any]) -> dict[str, Any]:
    nested = data.get("data") or data.get("result") or data.get("output")
    if isinstance(nested, list) and nested:
        first = nested[0]
        return first if isinstance(first, dict) else {}
    if isinstance(nested, dict):
        return nested
    return data


def _parse_video_result(data: dict[str, Any]) -> dict[str, Any]:
    item = _first_item(data)
    status_data = dict(data)
    if not any(status_data.get(key) for key in ("status", "task_status", "state")):
        status_data.update({key: item.get(key) for key in ("status", "task_status", "state") if item.get(key)})
    result_url = (
        item.get("url")
        or item.get("video_url")
        or item.get("content_url")
        or item.get("result_url")
        or item.get("output_url")
        or data.get("url")
        or data.get("video_url")
    )
    return {
        "provider_task_id": data.get("id") or data.get("task_id") or item.get("id"),
        "status": _status_from_response(status_data),
        "result_url": result_url,
        "thumbnail_url": item.get("thumbnail_url") or item.get("cover_url") or data.get("thumbnail_url"),
        "duration_seconds": item.get("duration") or item.get("duration_seconds") or data.get("duration"),
        "width": item.get("width") or data.get("width"),
        "height": item.get("height") or data.get("height"),
        "error_message": item.get("error_message") or data.get("error_message") or data.get("message"),
    }


async def _submit_to_provider(config: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    endpoint = config.get("endpoint_path") or "/contents/generations/tasks"
    url = _join_api_url(config["api_base_url"], endpoint)
    headers = {"Authorization": f"Bearer {config['api_key_secret']}"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


async def _refresh_from_provider(config: dict[str, Any], task_id: str) -> dict[str, Any]:
    endpoint = config.get("endpoint_path") or "/contents/generations/tasks"
    url = _join_api_url(config["api_base_url"], f"{endpoint.rstrip('/')}/{task_id}")
    headers = {"Authorization": f"Bearer {config['api_key_secret']}"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def list_video_generations(project_id: str, episode_no: int, shot_id: str) -> list[dict[str, Any]]:
    with get_session() as session:
        shot, prompt = _shot_and_prompt(session, project_id, episode_no, shot_id)
        generations = session.scalars(
            select(ProjectShotVideoGeneration)
            .where(ProjectShotVideoGeneration.shot_id == shot_id)
            .order_by(ProjectShotVideoGeneration.created_at.desc())
        ).all()
        return [_serialize_generation(generation, shot.revision, prompt.source_shot_revision if prompt else None) for generation in generations]


async def create_video_generation(project_id: str, episode_no: int, shot_id: str) -> dict[str, Any]:
    config = _enabled_video_config()
    with get_session() as session:
        shot, prompt = _shot_and_prompt(session, project_id, episode_no, shot_id)
        prompt_text = _prompt_text(prompt)
        request_payload = _request_payload(config, shot, prompt, prompt_text)
        now = now_utc()
        generation = ProjectShotVideoGeneration(
            id=str(uuid4()),
            project_id=project_id,
            episode_no=episode_no,
            storyboard_id=shot.storyboard_id,
            shot_id=shot.id,
            prompt_id=prompt.id if prompt else None,
            source_shot_revision=shot.revision,
            source_prompt_revision=prompt.source_shot_revision if prompt else None,
            video_prompt_snapshot=prompt_text,
            negative_prompt_snapshot=prompt.negative_prompt if prompt else None,
            reference_asset_ids=prompt.reference_asset_ids if prompt else "[]",
            model_config_id=config["id"],
            model_name=config["model_name"],
            provider_preset=config.get("provider_preset"),
            status="queued",
            request_payload_snapshot=json.dumps(_redact_payload(request_payload), ensure_ascii=False),
            adopted=False,
            created_at=now,
            updated_at=now,
        )
        session.add(generation)
        generation_id = generation.id

    started = perf_counter()
    try:
        provider_data = await _submit_to_provider(config, request_payload)
        parsed = _parse_video_result(provider_data)
        status = parsed["status"]
        if parsed["result_url"]:
            status = "succeeded"
        error_message = parsed["error_message"] if status == "failed" else None
    except httpx.HTTPStatusError as exc:
        parsed = {}
        status = "failed"
        error_message = _http_error_message(exc)
    except httpx.RequestError:
        parsed = {}
        status = "failed"
        error_message = "视频生成接口无法访问，请检查 API 地址或网络连接"
    except Exception:
        parsed = {}
        status = "failed"
        error_message = "视频生成任务创建失败，请检查模型配置"

    elapsed_ms = int((perf_counter() - started) * 1000)
    with get_session() as session:
        generation = session.get(ProjectShotVideoGeneration, generation_id)
        if not generation:
            raise ValueError("视频生成记录不存在")
        generation.provider_task_id = parsed.get("provider_task_id")
        generation.status = status
        generation.result_url = parsed.get("result_url")
        generation.thumbnail_url = parsed.get("thumbnail_url")
        generation.duration_seconds = _optional_float(parsed.get("duration_seconds"))
        generation.width = _optional_int(parsed.get("width"))
        generation.height = _optional_int(parsed.get("height"))
        generation.error_message = error_message
        generation.elapsed_ms = elapsed_ms
        generation.updated_at = now_utc()
        shot, prompt = _shot_and_prompt(session, project_id, episode_no, shot_id)
        return _serialize_generation(generation, shot.revision, prompt.source_shot_revision if prompt else None)


async def refresh_video_generation(project_id: str, episode_no: int, shot_id: str, generation_id: str) -> dict[str, Any]:
    with get_session() as session:
        generation = _generation_for_shot(session, project_id, episode_no, shot_id, generation_id)
        if generation.status not in ACTIVE_STATUSES or not generation.provider_task_id:
            shot, prompt = _shot_and_prompt(session, project_id, episode_no, shot_id)
            return _serialize_generation(generation, shot.revision, prompt.source_shot_revision if prompt else None)
        task_id = generation.provider_task_id
        model_config_id = generation.model_config_id

    config = _video_config_by_id(model_config_id)

    try:
        provider_data = await _refresh_from_provider(config, task_id)
        parsed = _parse_video_result(provider_data)
        error_message = parsed["error_message"] if parsed["status"] == "failed" else None
    except httpx.HTTPStatusError as exc:
        parsed = {"status": "failed"}
        error_message = _http_error_message(exc)
    except httpx.RequestError:
        parsed = {"status": "failed"}
        error_message = "视频生成接口无法访问，请稍后重试"
    except Exception:
        parsed = {"status": "failed"}
        error_message = "视频生成状态刷新失败"

    with get_session() as session:
        generation = _generation_for_shot(session, project_id, episode_no, shot_id, generation_id)
        generation.status = "succeeded" if parsed.get("result_url") else parsed.get("status", generation.status)
        generation.result_url = parsed.get("result_url") or generation.result_url
        generation.thumbnail_url = parsed.get("thumbnail_url") or generation.thumbnail_url
        generation.duration_seconds = _optional_float(parsed.get("duration_seconds")) or generation.duration_seconds
        generation.width = _optional_int(parsed.get("width")) or generation.width
        generation.height = _optional_int(parsed.get("height")) or generation.height
        generation.error_message = error_message
        generation.updated_at = now_utc()
        shot, prompt = _shot_and_prompt(session, project_id, episode_no, shot_id)
        return _serialize_generation(generation, shot.revision, prompt.source_shot_revision if prompt else None)


def adopt_video_generation(project_id: str, episode_no: int, shot_id: str, generation_id: str) -> dict[str, Any]:
    with get_session() as session:
        generation = _generation_for_shot(session, project_id, episode_no, shot_id, generation_id)
        if generation.status != "succeeded" or not (generation.result_url or generation.local_asset_path):
            raise ValueError("只能采用已成功生成的视频结果")
        now = now_utc()
        session.execute(
            update(ProjectShotVideoGeneration)
            .where(ProjectShotVideoGeneration.shot_id == shot_id)
            .values(adopted=False, adopted_at=None, updated_at=now)
        )
        generation.adopted = True
        generation.adopted_at = now
        generation.updated_at = now
        shot, prompt = _shot_and_prompt(session, project_id, episode_no, shot_id)
        return _serialize_generation(generation, shot.revision, prompt.source_shot_revision if prompt else None)


def cancel_video_generation(project_id: str, episode_no: int, shot_id: str, generation_id: str) -> dict[str, Any]:
    with get_session() as session:
        generation = _generation_for_shot(session, project_id, episode_no, shot_id, generation_id)
        if generation.status in ACTIVE_STATUSES:
            generation.status = "canceled"
            generation.updated_at = now_utc()
        shot, prompt = _shot_and_prompt(session, project_id, episode_no, shot_id)
        return _serialize_generation(generation, shot.revision, prompt.source_shot_revision if prompt else None)


def _optional_int(value) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _optional_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, ensure_ascii=False))


def _http_error_message(exc: httpx.HTTPStatusError) -> str:
    detail = ""
    try:
        data = exc.response.json()
        detail = data.get("message") or data.get("error", {}).get("message") or str(data)[:240]
    except Exception:
        detail = exc.response.text[:240]
    base = f"视频生成接口返回错误状态：{exc.response.status_code}"
    return f"{base}；响应：{detail}" if detail else base
