"""项目管理路由模块，提供项目列表、详情、创建和基础信息更新接口。"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project import management

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[dict]:
    """读取项目列表，并按最近更新时间排序。"""
    return management.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> dict:
    """读取项目详情，不存在时抛出业务错误。"""
    try:
        return management.get_project(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=ProjectResponse)
def create_project(payload: ProjectCreate) -> dict:
    """创建短剧项目，并写入总时长等计算字段。"""
    try:
        return management.create_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, payload: ProjectUpdate) -> dict:
    """更新项目基础信息，并标记下游创作内容需要复核。"""
    try:
        return management.update_project(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
