"""故事大纲路由模块，管理项目故事大纲生成、编辑、改写和参考结构提取。"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ProjectStoryOutlinePayload,
    ProjectStoryOutlineResponse,
    ReferenceStoryStructureApplyPayload,
    ReferenceStoryStructureDraftResponse,
    ReferenceStoryStructureExtractPayload,
    StoryOutlineAssistPayload,
    StoryOutlineAssistResult,
    StoryOutlineGenerationResult,
    StoryOutlineGeneratePayload,
    StoryOutlineRewritePayload,
    StoryOutlineRewriteResult,
)
from app.services.project.story import outline

router = APIRouter()


@router.get("/{project_id}/story-outline", response_model=ProjectStoryOutlineResponse | None)
def get_story_outline(project_id: str) -> dict | None:
    """读取项目故事大纲，未创建时返回空结果。"""
    try:
        return outline.get_story_outline(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/story-outline", response_model=ProjectStoryOutlineResponse)
def upsert_story_outline(project_id: str, payload: ProjectStoryOutlinePayload) -> dict:
    """创建或更新项目故事大纲，并标记下游内容需要复核。"""
    try:
        return outline.upsert_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/generate", response_model=StoryOutlineGenerationResult)
async def generate_story_outline(project_id: str, payload: StoryOutlineGeneratePayload) -> dict:
    """调用文本模型生成项目整体故事大纲。"""
    try:
        return await outline.generate_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/rewrite", response_model=StoryOutlineRewriteResult)
async def rewrite_story_outline(project_id: str, payload: StoryOutlineRewritePayload) -> dict:
    """调用文本模型局部改写故事大纲指定字段。"""
    try:
        return await outline.rewrite_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "整体故事大纲不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/assist", response_model=StoryOutlineAssistResult, response_model_exclude_none=True)
async def assist_story_outline(project_id: str, payload: StoryOutlineAssistPayload) -> dict:
    """调用文本模型根据对话辅助补全故事大纲。"""
    try:
        return await outline.assist_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-structure-drafts/extract", response_model=ReferenceStoryStructureDraftResponse)
async def extract_reference_story_structure(project_id: str, payload: ReferenceStoryStructureExtractPayload) -> dict:
    """从参考文本中抽取可复用故事结构草稿。"""
    try:
        return await outline.extract_reference_story_structure(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/story-structure-drafts", response_model=list[ReferenceStoryStructureDraftResponse])
def list_reference_story_structure_drafts(project_id: str) -> list[dict]:
    """列出项目内参考故事结构草稿。"""
    try:
        return outline.list_reference_story_structure_drafts(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/story-structure-drafts/{draft_id}", response_model=ReferenceStoryStructureDraftResponse)
def get_reference_story_structure_draft(project_id: str, draft_id: str) -> dict:
    """读取单个参考故事结构草稿。"""
    try:
        return outline.get_reference_story_structure_draft(project_id, draft_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-structure-drafts/{draft_id}/apply", response_model=ProjectStoryOutlineResponse)
def apply_reference_story_structure_draft(
    project_id: str,
    draft_id: str,
    payload: ReferenceStoryStructureApplyPayload,
) -> dict:
    """把参考结构草稿应用为当前项目故事大纲。"""
    try:
        return outline.apply_reference_story_structure_draft(project_id, draft_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-structure-drafts/{draft_id}/discard", response_model=ReferenceStoryStructureDraftResponse)
def discard_reference_story_structure_draft(project_id: str, draft_id: str) -> dict:
    """丢弃参考结构草稿，仅影响当前项目草稿状态。"""
    try:
        return outline.discard_reference_story_structure_draft(project_id, draft_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
