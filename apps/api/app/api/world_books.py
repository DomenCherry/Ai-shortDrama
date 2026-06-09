"""世界观路由模块，提供可复用世界观资产、条目和项目加载接口。"""
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
    """读取世界观资产列表，并支持状态与关键词过滤。"""
    return world_books.list_world_books(search=search, genre=genre, status=status)


@router.post("/world-books", response_model=WorldBookResponse)
def create_world_book(payload: WorldBookCreate) -> dict:
    """创建可复用世界观资产。"""
    return world_books.create_world_book(payload)


@router.get("/world-books/{world_book_id}", response_model=WorldBookResponse)
def get_world_book(world_book_id: str) -> dict:
    """读取单个世界观资产详情。"""
    try:
        return world_books.get_world_book(world_book_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/world-books/{world_book_id}", response_model=WorldBookResponse)
def update_world_book(world_book_id: str, payload: WorldBookUpdate) -> dict:
    """更新世界观资产，并递增版本用于项目快照来源追踪。"""
    try:
        return world_books.update_world_book(world_book_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/archive", response_model=WorldBookResponse)
def archive_world_book(world_book_id: str) -> dict:
    """归档世界观资产，保留历史项目引用。"""
    try:
        return world_books.archive_world_book(world_book_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/activate", response_model=WorldBookResponse)
def activate_world_book(world_book_id: str) -> dict:
    """恢复世界观资产为可加载状态。"""
    try:
        return world_books.activate_world_book(world_book_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/world-books/{world_book_id}/entries", response_model=list[WorldEntryResponse])
def list_world_entries(world_book_id: str) -> list[dict]:
    """读取指定世界观下的条目列表。"""
    try:
        return world_books.list_world_entries(world_book_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/entries", response_model=WorldEntryResponse)
def create_world_entry(world_book_id: str, payload: WorldEntryCreate) -> dict:
    """创建世界观条目，并同步递增世界观版本。"""
    try:
        return world_books.create_world_entry(world_book_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/world-books/{world_book_id}/entries/{entry_id}", response_model=WorldEntryResponse)
def update_world_entry(world_book_id: str, entry_id: str, payload: WorldEntryUpdate) -> dict:
    """更新世界观条目，并同步递增世界观版本。"""
    try:
        return world_books.update_world_entry(world_book_id, entry_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/entries/{entry_id}/disable", response_model=WorldEntryResponse)
def disable_world_entry(world_book_id: str, entry_id: str) -> dict:
    """停用世界观条目，保留条目用于后续恢复。"""
    try:
        return world_books.disable_world_entry(world_book_id, entry_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/world-books/{world_book_id}/entries/{entry_id}/enable", response_model=WorldEntryResponse)
def enable_world_entry(world_book_id: str, entry_id: str) -> dict:
    """启用世界观条目，使其可进入项目快照加载范围。"""
    try:
        return world_books.enable_world_entry(world_book_id, entry_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/projects/{project_id}/world-snapshots",
    response_model=ProjectWorldSnapshotResponse,
)
def load_world_book_to_project(project_id: str, payload: ProjectWorldSnapshotCreate) -> dict:
    """把世界观和启用条目复制为项目内快照，后续编辑不回写资产库。"""
    try:
        return world_books.load_world_book_to_project(project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
