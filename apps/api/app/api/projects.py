from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ProjectCharacterSnapshotUpdate,
    ProjectCopywritingPayload,
    ProjectCopywritingResponse,
    ProjectCharacterSnapshotResponse,
    ProjectCreate,
    ProjectEpisodeContentPayload,
    ProjectEpisodeContentResponse,
    ProjectEpisodeOutlinePayload,
    ProjectEpisodeOutlineResponse,
    ProjectEpisodeScriptPayload,
    ProjectEpisodeScriptResponse,
    ProjectResponse,
    ProjectStoryboardShotPayload,
    ProjectStoryboardShotResponse,
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
    ProjectUpdate,
    ProjectWorldSnapshotUpdate,
    ProjectWorldSnapshotResponse,
)
from app.services import projects

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[dict]:
    return projects.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> dict:
    try:
        return projects.get_project(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=ProjectResponse)
def create_project(payload: ProjectCreate) -> dict:
    try:
        return projects.create_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, payload: ProjectUpdate) -> dict:
    try:
        return projects.update_project(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/world-snapshots", response_model=list[ProjectWorldSnapshotResponse])
def list_project_world_snapshots(project_id: str) -> list[dict]:
    try:
        return projects.list_project_world_snapshots(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}/world-snapshots/{snapshot_id}")
def delete_project_world_snapshot(project_id: str, snapshot_id: str) -> dict:
    try:
        return projects.delete_project_world_snapshot(project_id, snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/world-snapshots/{snapshot_id}", response_model=ProjectWorldSnapshotResponse)
def update_project_world_snapshot(project_id: str, snapshot_id: str, payload: ProjectWorldSnapshotUpdate) -> dict:
    try:
        return projects.update_project_world_snapshot(project_id, snapshot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目世界观不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/character-snapshots", response_model=list[ProjectCharacterSnapshotResponse])
def list_project_character_snapshots(project_id: str) -> list[dict]:
    try:
        return projects.list_project_character_snapshots(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}/character-snapshots/{snapshot_id}")
def delete_project_character_snapshot(project_id: str, snapshot_id: str) -> dict:
    try:
        return projects.delete_project_character_snapshot(project_id, snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/character-snapshots/{snapshot_id}", response_model=ProjectCharacterSnapshotResponse)
def update_project_character_snapshot(project_id: str, snapshot_id: str, payload: ProjectCharacterSnapshotUpdate) -> dict:
    try:
        return projects.update_project_character_snapshot(project_id, snapshot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目角色不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/story-outline", response_model=ProjectStoryOutlineResponse | None)
def get_story_outline(project_id: str) -> dict | None:
    try:
        return projects.get_story_outline(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/story-outline", response_model=ProjectStoryOutlineResponse)
def upsert_story_outline(project_id: str, payload: ProjectStoryOutlinePayload) -> dict:
    try:
        return projects.upsert_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/generate", response_model=StoryOutlineGenerationResult)
async def generate_story_outline(project_id: str, payload: StoryOutlineGeneratePayload) -> dict:
    try:
        return await projects.generate_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/rewrite", response_model=StoryOutlineRewriteResult)
async def rewrite_story_outline(project_id: str, payload: StoryOutlineRewritePayload) -> dict:
    try:
        return await projects.rewrite_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "整体故事大纲不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-outline/assist", response_model=StoryOutlineAssistResult, response_model_exclude_none=True)
async def assist_story_outline(project_id: str, payload: StoryOutlineAssistPayload) -> dict:
    try:
        return await projects.assist_story_outline(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-structure-drafts/extract", response_model=ReferenceStoryStructureDraftResponse)
async def extract_reference_story_structure(project_id: str, payload: ReferenceStoryStructureExtractPayload) -> dict:
    try:
        return await projects.extract_reference_story_structure(project_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/story-structure-drafts", response_model=list[ReferenceStoryStructureDraftResponse])
def list_reference_story_structure_drafts(project_id: str) -> list[dict]:
    try:
        return projects.list_reference_story_structure_drafts(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/story-structure-drafts/{draft_id}", response_model=ReferenceStoryStructureDraftResponse)
def get_reference_story_structure_draft(project_id: str, draft_id: str) -> dict:
    try:
        return projects.get_reference_story_structure_draft(project_id, draft_id)
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
        return projects.apply_reference_story_structure_draft(project_id, draft_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/story-structure-drafts/{draft_id}/discard", response_model=ReferenceStoryStructureDraftResponse)
def discard_reference_story_structure_draft(project_id: str, draft_id: str) -> dict:
    try:
        return projects.discard_reference_story_structure_draft(project_id, draft_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "参考框架草稿不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/episode-outlines", response_model=list[ProjectEpisodeOutlineResponse])
def list_episode_outlines(project_id: str) -> list[dict]:
    try:
        return projects.list_episode_outlines(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{project_id}/episode-outlines/{episode_no}", response_model=ProjectEpisodeOutlineResponse)
def upsert_episode_outline(project_id: str, episode_no: int, payload: ProjectEpisodeOutlinePayload) -> dict:
    try:
        return projects.upsert_episode_outline(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/episode-contents/{episode_no}", response_model=ProjectEpisodeContentResponse | None)
def get_episode_content(project_id: str, episode_no: int) -> dict | None:
    try:
        return projects.get_episode_content(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/episode-contents/{episode_no}", response_model=ProjectEpisodeContentResponse)
def upsert_episode_content(project_id: str, episode_no: int, payload: ProjectEpisodeContentPayload) -> dict:
    try:
        return projects.upsert_episode_content(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/episode-scripts/{episode_no}", response_model=ProjectEpisodeScriptResponse | None)
def get_episode_script(project_id: str, episode_no: int) -> dict | None:
    try:
        return projects.get_episode_script(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/episode-scripts/{episode_no}", response_model=ProjectEpisodeScriptResponse)
def upsert_episode_script(project_id: str, episode_no: int, payload: ProjectEpisodeScriptPayload) -> dict:
    try:
        return projects.upsert_episode_script(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/storyboard-shots/{episode_no}", response_model=list[ProjectStoryboardShotResponse])
def list_storyboard_shots(project_id: str, episode_no: int) -> list[dict]:
    try:
        return projects.list_storyboard_shots(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/storyboard-shots/{episode_no}", response_model=ProjectStoryboardShotResponse)
def create_storyboard_shot(project_id: str, episode_no: int, payload: ProjectStoryboardShotPayload) -> dict:
    try:
        return projects.create_storyboard_shot(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/storyboard-shots/{episode_no}/{shot_id}", response_model=ProjectStoryboardShotResponse)
def update_storyboard_shot(project_id: str, episode_no: int, shot_id: str, payload: ProjectStoryboardShotPayload) -> dict:
    try:
        return projects.update_storyboard_shot(project_id, episode_no, shot_id, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目分镜不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/{project_id}/storyboard-shots/{episode_no}/{shot_id}")
def delete_storyboard_shot(project_id: str, episode_no: int, shot_id: str) -> dict:
    try:
        return projects.delete_storyboard_shot(project_id, episode_no, shot_id)
    except ValueError as exc:
        status_code = 404 if str(exc) in {"项目不存在", "项目分镜不存在"} else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/copywriting/{episode_no}", response_model=ProjectCopywritingResponse | None)
def get_copywriting(project_id: str, episode_no: int) -> dict | None:
    try:
        return projects.get_copywriting(project_id, episode_no)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/{project_id}/copywriting/{episode_no}", response_model=ProjectCopywritingResponse)
def upsert_copywriting(project_id: str, episode_no: int, payload: ProjectCopywritingPayload) -> dict:
    try:
        return projects.upsert_copywriting(project_id, episode_no, payload)
    except ValueError as exc:
        status_code = 404 if str(exc) == "项目不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
