"""结构化剧本路由。"""
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.schemas import (
    ProjectEpisodeScriptPayload,
    ProjectEpisodeScriptResponse,
    ScriptCheckPayload,
    ScriptCheckResponse,
    ScriptGenerationAdoptResponse,
    ScriptGenerationCreate,
    ScriptGenerationResponse,
    ScriptRevisionPayload,
    ScriptVersionSummary,
)
from app.services.project.story import episode_scripts

router = APIRouter()


def _raise(exc: ValueError) -> None:
    if isinstance(exc, episode_scripts.ScriptConflictError):
        status = 409
    elif isinstance(exc, episode_scripts.ScriptValidationError):
        status = 422
    elif str(exc) in {"项目不存在", "正式剧本不存在", "剧本候选不存在", "剧本历史版本不存在"}:
        status = 404
    else:
        status = 400
    detail = {"message": str(exc), "issues": getattr(exc, "issues", [])}
    raise HTTPException(status_code=status, detail=detail) from exc


def _raise_integrity(exc: IntegrityError) -> None:
    """数据库约束异常不暴露 SQL 和参数，只返回可恢复的业务提示。"""
    raise HTTPException(
        status_code=409,
        detail={"message": "剧本写入发生数据冲突，请刷新后重试", "issues": []},
    ) from exc


@router.get("/{project_id}/episode-scripts/{episode_no}", response_model=ProjectEpisodeScriptResponse | None)
def get_episode_script(project_id: str, episode_no: int) -> dict | None:
    try:
        return episode_scripts.get_episode_script(project_id, episode_no)
    except ValueError as exc:
        _raise(exc)


@router.put("/{project_id}/episode-scripts/{episode_no}", response_model=ProjectEpisodeScriptResponse)
def upsert_episode_script(project_id: str, episode_no: int, payload: ProjectEpisodeScriptPayload) -> dict:
    try:
        return episode_scripts.upsert_episode_script(project_id, episode_no, payload)
    except IntegrityError as exc:
        _raise_integrity(exc)
    except ValueError as exc:
        _raise(exc)


@router.post("/{project_id}/episode-scripts/{episode_no}/generations", response_model=ScriptGenerationResponse)
async def generate_episode_script(project_id: str, episode_no: int, payload: ScriptGenerationCreate) -> dict:
    try:
        return await episode_scripts.generate_episode_script(project_id, episode_no, payload)
    except ValueError as exc:
        _raise(exc)


@router.get("/{project_id}/episode-scripts/{episode_no}/generations", response_model=list[ScriptGenerationResponse])
def list_script_generations(project_id: str, episode_no: int) -> list[dict]:
    try:
        return episode_scripts.list_script_generations(project_id, episode_no)
    except ValueError as exc:
        _raise(exc)


@router.get("/{project_id}/episode-scripts/{episode_no}/generations/{generation_id}", response_model=ScriptGenerationResponse)
def get_script_generation(project_id: str, episode_no: int, generation_id: str) -> dict:
    try:
        return episode_scripts.get_script_generation(project_id, episode_no, generation_id)
    except ValueError as exc:
        _raise(exc)


@router.post("/{project_id}/episode-scripts/{episode_no}/generations/{generation_id}/adopt", response_model=ScriptGenerationAdoptResponse)
def adopt_script_generation(project_id: str, episode_no: int, generation_id: str, payload: ScriptRevisionPayload) -> dict:
    try:
        return episode_scripts.adopt_script_generation(project_id, episode_no, generation_id, payload)
    except IntegrityError as exc:
        _raise_integrity(exc)
    except ValueError as exc:
        _raise(exc)


@router.post("/{project_id}/episode-scripts/{episode_no}/generations/{generation_id}/discard", response_model=ScriptGenerationResponse)
def discard_script_generation(project_id: str, episode_no: int, generation_id: str) -> dict:
    try:
        return episode_scripts.discard_script_generation(project_id, episode_no, generation_id)
    except ValueError as exc:
        _raise(exc)


@router.post("/{project_id}/episode-scripts/{episode_no}/checks", response_model=ScriptCheckResponse)
async def check_episode_script(project_id: str, episode_no: int, payload: ScriptCheckPayload) -> dict:
    try:
        return await episode_scripts.check_episode_script(project_id, episode_no, payload)
    except ValueError as exc:
        _raise(exc)


@router.post("/{project_id}/episode-scripts/{episode_no}/submit-review", response_model=ProjectEpisodeScriptResponse)
def submit_episode_script(project_id: str, episode_no: int, payload: ScriptRevisionPayload) -> dict:
    try:
        return episode_scripts.submit_episode_script(project_id, episode_no, payload)
    except ValueError as exc:
        _raise(exc)


@router.post("/{project_id}/episode-scripts/{episode_no}/confirm", response_model=ProjectEpisodeScriptResponse)
def confirm_episode_script(project_id: str, episode_no: int, payload: ScriptRevisionPayload) -> dict:
    try:
        return episode_scripts.confirm_episode_script(project_id, episode_no, payload)
    except ValueError as exc:
        _raise(exc)


@router.get("/{project_id}/episode-scripts/{episode_no}/versions", response_model=list[ScriptVersionSummary])
def list_episode_script_versions(project_id: str, episode_no: int) -> list[dict]:
    try:
        return episode_scripts.list_episode_script_versions(project_id, episode_no)
    except ValueError as exc:
        _raise(exc)


@router.get("/{project_id}/episode-scripts/{episode_no}/versions/{version}")
def get_episode_script_version(project_id: str, episode_no: int, version: int) -> dict:
    try:
        return episode_scripts.get_episode_script_version(project_id, episode_no, version)
    except ValueError as exc:
        _raise(exc)
