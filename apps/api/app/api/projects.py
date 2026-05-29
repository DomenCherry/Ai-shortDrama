from fastapi import APIRouter, HTTPException

from app.models.schemas import ProjectCreate, ProjectResponse
from app.services import projects

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[dict]:
    return projects.list_projects()


@router.post("", response_model=ProjectResponse)
def create_project(payload: ProjectCreate) -> dict:
    try:
        return projects.create_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

