"""单集正文路由模块，管理项目每集详细故事正文的读取和保存。"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    EpisodeContentGenerationAdoptResponse,
    EpisodeContentGenerationCreate,
    EpisodeContentGenerationResponse,
    EpisodeContentGenerationUpdate,
    ProjectEpisodeContentPayload,
    ProjectEpisodeContentResponse,
)
from app.services.project.story import episode_contents

router = APIRouter()


@router.get("/{project_id}/episode-contents/{episode_no}", response_model=ProjectEpisodeContentResponse | None)
def get_episode_content(project_id: str, episode_no: int) -> dict | None:
    """读取指定集数的详细故事正文。"""
    try:
        return episode_contents.get_episode_content(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/episode-contents/{episode_no}", response_model=ProjectEpisodeContentResponse)
def upsert_episode_content(project_id: str, episode_no: int, payload: ProjectEpisodeContentPayload) -> dict:
    """创建或更新指定集数正文，并同步字数和下游复核状态。"""
    try:
        return episode_contents.upsert_episode_content(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post(
    "/{project_id}/episode-contents/{episode_no}/generations",
    response_model=EpisodeContentGenerationResponse,
)
async def generate_episode_content(
    project_id: str,
    episode_no: int,
    payload: EpisodeContentGenerationCreate,
) -> dict:
    """基于项目上下文生成并持久化单集正文候选稿。"""
    try:
        return await episode_contents.generate_episode_content(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get(
    "/{project_id}/episode-contents/{episode_no}/generations",
    response_model=list[EpisodeContentGenerationResponse],
)
def list_episode_content_generations(project_id: str, episode_no: int) -> list[dict]:
    """读取当前集最近的正文生成版本。"""
    try:
        return episode_contents.list_episode_content_generations(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put(
    "/{project_id}/episode-contents/{episode_no}/generations/{generation_id}",
    response_model=EpisodeContentGenerationResponse,
)
def update_episode_content_generation(
    project_id: str,
    episode_no: int,
    generation_id: str,
    payload: EpisodeContentGenerationUpdate,
) -> dict:
    """保存候选稿人工编辑。"""
    try:
        return episode_contents.update_episode_content_generation(project_id, episode_no, generation_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "正文候选版本不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post(
    "/{project_id}/episode-contents/{episode_no}/generations/{generation_id}/adopt",
    response_model=EpisodeContentGenerationAdoptResponse,
)
def adopt_episode_content_generation(project_id: str, episode_no: int, generation_id: str) -> dict:
    """采用候选稿并原子更新正式正文。"""
    try:
        return episode_contents.adopt_episode_content_generation(project_id, episode_no, generation_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "正文候选版本不存在"} else 409 if "已在候选稿生成后更新" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post(
    "/{project_id}/episode-contents/{episode_no}/generations/{generation_id}/discard",
    response_model=EpisodeContentGenerationResponse,
)
def discard_episode_content_generation(project_id: str, episode_no: int, generation_id: str) -> dict:
    """放弃候选稿但保留历史记录。"""
    try:
        return episode_contents.discard_episode_content_generation(project_id, episode_no, generation_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "正文候选版本不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
