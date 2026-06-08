from fastapi import APIRouter, HTTPException

from app.models.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project import management

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[dict]:
    return management.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> dict:
    try:
        return management.get_project(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=ProjectResponse)
def create_project(payload: ProjectCreate) -> dict:
    try:
        return management.create_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, payload: ProjectUpdate) -> dict:
    try:
        return management.update_project(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
