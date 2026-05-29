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
    return character_cards.list_character_cards(search=search, gender=gender, role_type=role_type, status=status)


@router.post("/character-cards", response_model=CharacterCardResponse)
def create_character_card(payload: CharacterCardCreate) -> dict:
    return character_cards.create_character_card(payload)


@router.get("/character-cards/{card_id}", response_model=CharacterCardResponse)
def get_character_card(card_id: str) -> dict:
    try:
        return character_cards.get_character_card(card_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/character-cards/{card_id}", response_model=CharacterCardResponse)
def update_character_card(card_id: str, payload: CharacterCardUpdate) -> dict:
    try:
        return character_cards.update_character_card(card_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/archive", response_model=CharacterCardResponse)
def archive_character_card(card_id: str) -> dict:
    try:
        return character_cards.archive_character_card(card_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/activate", response_model=CharacterCardResponse)
def activate_character_card(card_id: str) -> dict:
    try:
        return character_cards.activate_character_card(card_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/reference-images", response_model=CharacterImageAssetResponse)
def upload_reference_image(card_id: str, payload: CharacterReferenceImageUpload) -> dict:
    try:
        return character_cards.upload_reference_image(card_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/turnaround-images", response_model=CharacterTurnaroundResponse)
async def generate_turnaround_image(card_id: str, payload: CharacterTurnaroundGenerate) -> dict:
    try:
        return await character_cards.generate_turnaround_image(card_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/character-cards/{card_id}/turnaround-images/confirm", response_model=CharacterTurnaroundResponse)
def confirm_turnaround_image(card_id: str) -> dict:
    try:
        return character_cards.confirm_turnaround_image(card_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/character-cards/{card_id}/turnaround-images/{image_id}/confirm",
    response_model=CharacterTurnaroundResponse,
)
def confirm_turnaround_image_by_id(card_id: str, image_id: str) -> dict:
    try:
        return character_cards.confirm_turnaround_image(card_id, image_id=image_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/projects/{project_id}/character-snapshots",
    response_model=ProjectCharacterSnapshotResponse,
)
def load_character_card_to_project(project_id: str, payload: ProjectCharacterSnapshotCreate) -> dict:
    try:
        return character_cards.load_character_card_to_project(project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
