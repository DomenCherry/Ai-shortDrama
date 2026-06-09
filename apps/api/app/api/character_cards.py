"""角色卡路由模块，提供可复用人物资产的管理、素材上传和项目加载接口。"""
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    CharacterImageAssetResponse,
    CharacterCardCreate,
    CharacterCardResponse,
    CharacterCardUpdate,
    CharacterReferenceImageUpload,
    CharacterTurnaroundGenerate,
    CharacterTurnaroundResponse,
    ProjectCharacterSnapshotCreate,
    ProjectCharacterSnapshotResponse,
)
from app.services import character_cards

router = APIRouter(prefix="/api", tags=["character-cards"])


@router.get("/character-cards", response_model=list[CharacterCardResponse])
def list_character_cards(
    search: str | None = Query(default=None),
    gender: Literal["男", "女"] | None = Query(default=None),
    role_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> list[dict]:
    """读取角色卡列表，并支持状态与关键词过滤。"""
    return character_cards.list_character_cards(search=search, gender=gender, role_type=role_type, status=status)


@router.post("/character-cards", response_model=CharacterCardResponse)
def create_character_card(payload: CharacterCardCreate) -> dict:
    """创建可复用角色卡资产。"""
    return character_cards.create_character_card(payload)


@router.get("/character-cards/{card_id}", response_model=CharacterCardResponse)
def get_character_card(card_id: str) -> dict:
    """读取单个角色卡资产详情。"""
    try:
        return character_cards.get_character_card(card_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/character-cards/{card_id}", response_model=CharacterCardResponse)
def update_character_card(card_id: str, payload: CharacterCardUpdate) -> dict:
    """更新角色卡资产，并递增版本用于项目快照来源追踪。"""
    try:
        return character_cards.update_character_card(card_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/archive", response_model=CharacterCardResponse)
def archive_character_card(card_id: str) -> dict:
    """归档角色卡资产，保留历史项目引用。"""
    try:
        return character_cards.archive_character_card(card_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/activate", response_model=CharacterCardResponse)
def activate_character_card(card_id: str) -> dict:
    """恢复角色卡为可加载状态。"""
    try:
        return character_cards.activate_character_card(card_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/reference-images", response_model=CharacterImageAssetResponse)
def upload_reference_image(card_id: str, payload: CharacterReferenceImageUpload) -> dict:
    """上传角色参考图并绑定到角色卡资产。"""
    try:
        return character_cards.upload_reference_image(card_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/turnaround-images", response_model=CharacterTurnaroundResponse)
async def generate_turnaround_image(card_id: str, payload: CharacterTurnaroundGenerate) -> dict:
    """调用图片模型生成角色三视图，并记录生成结果。"""
    try:
        return await character_cards.generate_turnaround_image(card_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/turnaround-images/confirm", response_model=CharacterTurnaroundResponse)
def confirm_turnaround_image(card_id: str) -> dict:
    """确认当前或指定三视图为后续视频生成参考素材。"""
    try:
        return character_cards.confirm_turnaround_image(card_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/character-cards/{card_id}/turnaround-images/{image_id}/confirm",
    response_model=CharacterTurnaroundResponse,
)
def confirm_turnaround_image_by_id(card_id: str, image_id: str) -> dict:
    """确认用户选择的结果，作为后续流程的引用依据。"""
    try:
        return character_cards.confirm_turnaround_image(card_id, image_id=image_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/projects/{project_id}/character-snapshots",
    response_model=ProjectCharacterSnapshotResponse,
)
def load_character_card_to_project(project_id: str, payload: ProjectCharacterSnapshotCreate) -> dict:
    """把角色卡复制为项目内快照，后续编辑不回写原始资产。"""
    try:
        return character_cards.load_character_card_to_project(project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
