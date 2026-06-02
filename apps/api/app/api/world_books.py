from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    ProjectWorldSnapshotCreate,
    ProjectWorldSnapshotResponse,
    WorldBookCreate,
    WorldBookResponse,
    WorldBookUpdate,
    WorldEntryCreate,
    WorldEntryResponse,
    WorldEntryUpdate,
)
from app.services import world_books

router = APIRouter(prefix="/api", tags=["world-books"])


@router.get("/world-books", response_model=list[WorldBookResponse])
def list_world_books(
    search: str | None = Query(default=None),
    genre: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> list[dict]:
    return world_books.list_world_books(search=search, genre=genre, status=status)


@router.post("/world-books", response_model=WorldBookResponse)
def create_world_book(payload: WorldBookCreate) -> dict:
    return world_books.create_world_book(payload)


@router.get("/world-books/{world_book_id}", response_model=WorldBookResponse)
def get_world_book(world_book_id: str) -> dict:
    try:
        return world_books.get_world_book(world_book_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/world-books/{world_book_id}", response_model=WorldBookResponse)
def update_world_book(world_book_id: str, payload: WorldBookUpdate) -> dict:
    try:
        return world_books.update_world_book(world_book_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/archive", response_model=WorldBookResponse)
def archive_world_book(world_book_id: str) -> dict:
    try:
        return world_books.archive_world_book(world_book_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/activate", response_model=WorldBookResponse)
def activate_world_book(world_book_id: str) -> dict:
    try:
        return world_books.activate_world_book(world_book_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/world-books/{world_book_id}/entries", response_model=list[WorldEntryResponse])
def list_world_entries(world_book_id: str) -> list[dict]:
    try:
        return world_books.list_world_entries(world_book_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/entries", response_model=WorldEntryResponse)
def create_world_entry(world_book_id: str, payload: WorldEntryCreate) -> dict:
    try:
        return world_books.create_world_entry(world_book_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/world-books/{world_book_id}/entries/{entry_id}", response_model=WorldEntryResponse)
def update_world_entry(world_book_id: str, entry_id: str, payload: WorldEntryUpdate) -> dict:
    try:
        return world_books.update_world_entry(world_book_id, entry_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/entries/{entry_id}/disable", response_model=WorldEntryResponse)
def disable_world_entry(world_book_id: str, entry_id: str) -> dict:
    try:
        return world_books.disable_world_entry(world_book_id, entry_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/entries/{entry_id}/enable", response_model=WorldEntryResponse)
def enable_world_entry(world_book_id: str, entry_id: str) -> dict:
    try:
        return world_books.enable_world_entry(world_book_id, entry_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/projects/{project_id}/world-snapshots",
    response_model=ProjectWorldSnapshotResponse,
)
def load_world_book_to_project(project_id: str, payload: ProjectWorldSnapshotCreate) -> dict:
    try:
        return world_books.load_world_book_to_project(project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
