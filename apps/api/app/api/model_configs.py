from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    ModelApiConfigCreate,
    ModelApiConfigUpdate,
    ModelApiConfigResponse,
    ModelApiTestResponse,
)
from app.services import model_configs

router = APIRouter(prefix="/api/model-configs", tags=["model-configs"])


@router.get("", response_model=list[ModelApiConfigResponse])
def list_model_configs(config_type: str | None = Query(None)) -> list[dict]:
    configs = model_configs.list_configs()
    if config_type:
        return [c for c in configs if c["config_type"] == config_type]
    return configs


@router.get("/{config_id}", response_model=ModelApiConfigResponse)
def get_model_config(config_id: str) -> dict:
    try:
        return model_configs.get_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=ModelApiConfigResponse)
def create_model_config(payload: ModelApiConfigCreate) -> dict:
    try:
        return model_configs.create_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{config_id}", response_model=ModelApiConfigResponse)
def update_model_config(config_id: str, payload: ModelApiConfigUpdate) -> dict:
    try:
        return model_configs.update_config(config_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{config_id}")
def delete_model_config(config_id: str) -> dict:
    try:
        model_configs.delete_config(config_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{config_id}/enable", response_model=ModelApiConfigResponse)
def enable_model_config(config_id: str) -> dict:
    try:
        return model_configs.enable_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{config_id}/test", response_model=ModelApiTestResponse)
async def test_model_config(config_id: str) -> dict:
    try:
        return await model_configs.test_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
