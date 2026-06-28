"""模型配置路由模块，提供文本、图片和视频模型配置的增删改查与连通性测试。"""
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
    """读取模型配置列表，可按文本、图片或视频模型类型过滤。"""
    configs = model_configs.list_configs()
    if config_type:
        return [c for c in configs if c["config_type"] == config_type]
    return configs


@router.get("/{config_id}", response_model=ModelApiConfigResponse)
def get_model_config(config_id: str) -> dict:
    """读取单个模型配置，已软删除配置按不存在处理。"""
    try:
        return model_configs.get_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=ModelApiConfigResponse)
def create_model_config(payload: ModelApiConfigCreate) -> dict:
    """创建模型配置，密钥只进入服务端存储且响应中脱敏。"""
    try:
        return model_configs.create_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{config_id}", response_model=ModelApiConfigResponse)
def update_model_config(config_id: str, payload: ModelApiConfigUpdate) -> dict:
    """更新模型配置，并保持同类型启用配置的互斥规则。"""
    try:
        return model_configs.update_config(config_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{config_id}")
def delete_model_config(config_id: str) -> dict:
    """软删除模型配置，保留历史测试日志用于排查。"""
    try:
        model_configs.delete_config(config_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{config_id}/enable", response_model=ModelApiConfigResponse)
def enable_model_config(config_id: str) -> dict:
    """启用模型配置，并关闭同类型其他未删除配置。"""
    try:
        return model_configs.enable_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{config_id}/test", response_model=ModelApiTestResponse)
async def test_model_config(config_id: str) -> dict:
    """测试模型接口连通性，并返回用户可理解的测试结果。"""
    try:
        return await model_configs.test_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
