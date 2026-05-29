from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ModelApiConfigCreate,
    ModelApiConfigResponse,
    ModelApiTestResponse,
)
from app.services import model_configs

router = APIRouter(prefix="/api/model-configs", tags=["model-configs"])


@router.get("", response_model=list[ModelApiConfigResponse])
def list_model_configs() -> list[dict]:
    return model_configs.list_configs()


@router.post("", response_model=ModelApiConfigResponse)
def create_model_config(payload: ModelApiConfigCreate) -> dict:
    try:
        return model_configs.create_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{config_id}/test", response_model=ModelApiTestResponse)
async def test_model_config(config_id: str) -> dict:
    try:
        return await model_configs.test_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
