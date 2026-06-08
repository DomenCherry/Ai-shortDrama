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
    try:
        return outline.get_story_outline(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/story-outline", response_model=ProjectStoryOutlineResponse)
def upsert_story_outline(project_id: str, payload: ProjectStoryOutlinePayload) -> dict:
    try:
        return outline.upsert_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/generate", response_model=StoryOutlineGenerationResult)
async def generate_story_outline(project_id: str, payload: StoryOutlineGeneratePayload) -> dict:
    try:
        return await outline.generate_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/rewrite", response_model=StoryOutlineRewriteResult)
async def rewrite_story_outline(project_id: str, payload: StoryOutlineRewritePayload) -> dict:
    try:
        return await outline.rewrite_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "整体故事大纲不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/assist", response_model=StoryOutlineAssistResult, response_model_exclude_none=True)
async def assist_story_outline(project_id: str, payload: StoryOutlineAssistPayload) -> dict:
    try:
        return await outline.assist_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-structure-drafts/extract", response_model=ReferenceStoryStructureDraftResponse)
async def extract_reference_story_structure(project_id: str, payload: ReferenceStoryStructureExtractPayload) -> dict:
    try:
        return await outline.extract_reference_story_structure(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/story-structure-drafts", response_model=list[ReferenceStoryStructureDraftResponse])
def list_reference_story_structure_drafts(project_id: str) -> list[dict]:
    try:
        return outline.list_reference_story_structure_drafts(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/story-structure-drafts/{draft_id}", response_model=ReferenceStoryStructureDraftResponse)
def get_reference_story_structure_draft(project_id: str, draft_id: str) -> dict:
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
    try:
        return outline.apply_reference_story_structure_draft(project_id, draft_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-structure-drafts/{draft_id}/discard", response_model=ReferenceStoryStructureDraftResponse)
def discard_reference_story_structure_draft(project_id: str, draft_id: str) -> dict:
    try:
        return outline.discard_reference_story_structure_draft(project_id, draft_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
