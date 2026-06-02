from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import func, or_, select

from app.core.db import get_session
from app.models.db_models import Project, ProjectWorldSnapshot, WorldBook, WorldEntry
from app.models.schemas import (
    ProjectWorldSnapshotCreate,
    WorldBookCreate,
    WorldBookUpdate,
    WorldEntryCreate,
    WorldEntryUpdate,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _entry_counts(session, world_book_id: str) -> tuple[int, int]:
    entry_count = session.scalar(select(func.count()).select_from(WorldEntry).where(WorldEntry.world_book_id == world_book_id))
    active_entry_count = session.scalar(
        select(func.count()).select_from(WorldEntry).where(
            WorldEntry.world_book_id == world_book_id,
            WorldEntry.status == "active",
        )
    )
    return int(entry_count or 0), int(active_entry_count or 0)


def _world_book_to_response(book: WorldBook, entry_count: int = 0, active_entry_count: int = 0) -> dict[str, Any]:
    return {
        "id": book.id,
        "name": book.name,
        "genre": book.genre,
        "era_background": book.era_background,
        "world_rules": book.world_rules,
        "organizations": book.organizations,
        "locations": book.locations,
        "social_structure": book.social_structure,
        "taboo_or_constraints": book.taboo_or_constraints,
        "tone_style": book.tone_style,
        "summary": book.summary,
        "version": book.version,
        "status": book.status,
        "entry_count": entry_count,
        "active_entry_count": active_entry_count,
        "created_at": book.created_at.isoformat(),
        "updated_at": book.updated_at.isoformat(),
    }


def _world_entry_to_response(entry: WorldEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "world_book_id": entry.world_book_id,
        "title": entry.title,
        "entry_type": entry.entry_type,
        "keywords": entry.keywords,
        "content": entry.content,
        "applicable_scope": entry.applicable_scope,
        "priority": entry.priority,
        "status": entry.status,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
    }


def _snapshot_to_response(snapshot: ProjectWorldSnapshot) -> dict[str, Any]:
    return {
        "id": snapshot.id,
        "project_id": snapshot.project_id,
        "source_world_book_id": snapshot.source_world_book_id,
        "source_version": snapshot.source_version,
        "name": snapshot.name,
        "genre": snapshot.genre,
        "snapshot_content": snapshot.snapshot_content,
        "entry_snapshot_content": snapshot.entry_snapshot_content,
        "loaded_at": snapshot.loaded_at.isoformat(),
        "updated_at": snapshot.updated_at.isoformat(),
    }


def _payload_to_world_book_fields(payload: WorldBookCreate | WorldBookUpdate) -> dict[str, Any]:
    return {
        "name": payload.name,
        "genre": payload.genre,
        "era_background": payload.era_background,
        "world_rules": payload.world_rules,
        "organizations": payload.organizations,
        "locations": payload.locations,
        "social_structure": payload.social_structure,
        "taboo_or_constraints": payload.taboo_or_constraints,
        "tone_style": payload.tone_style,
        "summary": payload.summary,
        "status": payload.status,
    }


def _payload_to_world_entry_fields(payload: WorldEntryCreate | WorldEntryUpdate) -> dict[str, Any]:
    return {
        "title": payload.title,
        "entry_type": payload.entry_type,
        "keywords": payload.keywords,
        "content": payload.content,
        "applicable_scope": payload.applicable_scope,
        "priority": payload.priority,
        "status": payload.status,
    }


def _bump_world_book_version(book: WorldBook) -> None:
    book.version += 1
    book.updated_at = _now()


def list_world_books(
    search: Optional[str] = None,
    genre: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    with get_session() as session:
        statement = select(WorldBook)
        if search:
            keyword = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    WorldBook.name.ilike(keyword),
                    WorldBook.genre.ilike(keyword),
                    WorldBook.summary.ilike(keyword),
                )
            )
        if genre:
            statement = statement.where(WorldBook.genre == genre)
        if status:
            statement = statement.where(WorldBook.status == status)

        books = session.scalars(statement.order_by(WorldBook.updated_at.desc())).all()
        responses = []
        for book in books:
            entry_count, active_entry_count = _entry_counts(session, book.id)
            responses.append(_world_book_to_response(book, entry_count, active_entry_count))
        return responses


def create_world_book(payload: WorldBookCreate) -> dict[str, Any]:
    now = _now()
    book = WorldBook(
        id=str(uuid4()),
        **_payload_to_world_book_fields(payload),
        version=1,
        created_at=now,
        updated_at=now,
    )

    with get_session() as session:
        session.add(book)
        session.flush()
        return _world_book_to_response(book)


def get_world_book(world_book_id: str) -> dict[str, Any]:
    with get_session() as session:
        book = session.get(WorldBook, world_book_id)
        if not book:
            raise ValueError("世界观不存在")
        entry_count, active_entry_count = _entry_counts(session, book.id)
        return _world_book_to_response(book, entry_count, active_entry_count)


def update_world_book(world_book_id: str, payload: WorldBookUpdate) -> dict[str, Any]:
    with get_session() as session:
        book = session.get(WorldBook, world_book_id)
        if not book:
            raise ValueError("世界观不存在")

        fields = _payload_to_world_book_fields(payload)
        has_content_change = any(getattr(book, key) != value for key, value in fields.items())
        for key, value in fields.items():
            setattr(book, key, value)

        if has_content_change:
            _bump_world_book_version(book)
        else:
            book.updated_at = _now()
        session.flush()
        entry_count, active_entry_count = _entry_counts(session, book.id)
        return _world_book_to_response(book, entry_count, active_entry_count)


def archive_world_book(world_book_id: str) -> dict[str, Any]:
    with get_session() as session:
        book = session.get(WorldBook, world_book_id)
        if not book:
            raise ValueError("世界观不存在")

        if book.status != "archived":
            book.status = "archived"
            _bump_world_book_version(book)
        session.flush()
        entry_count, active_entry_count = _entry_counts(session, book.id)
        return _world_book_to_response(book, entry_count, active_entry_count)


def activate_world_book(world_book_id: str) -> dict[str, Any]:
    with get_session() as session:
        book = session.get(WorldBook, world_book_id)
        if not book:
            raise ValueError("世界观不存在")

        if book.status != "active":
            book.status = "active"
            _bump_world_book_version(book)
        session.flush()
        entry_count, active_entry_count = _entry_counts(session, book.id)
        return _world_book_to_response(book, entry_count, active_entry_count)


def list_world_entries(world_book_id: str) -> list[dict[str, Any]]:
    with get_session() as session:
        book = session.get(WorldBook, world_book_id)
        if not book:
            raise ValueError("世界观不存在")

        entries = session.scalars(
            select(WorldEntry)
            .where(WorldEntry.world_book_id == world_book_id)
            .order_by(WorldEntry.priority.desc(), WorldEntry.updated_at.desc())
        ).all()
        return [_world_entry_to_response(entry) for entry in entries]


def create_world_entry(world_book_id: str, payload: WorldEntryCreate) -> dict[str, Any]:
    now = _now()
    with get_session() as session:
        book = session.get(WorldBook, world_book_id)
        if not book:
            raise ValueError("世界观不存在")

        entry = WorldEntry(
            id=str(uuid4()),
            world_book_id=world_book_id,
            **_payload_to_world_entry_fields(payload),
            created_at=now,
            updated_at=now,
        )
        session.add(entry)
        _bump_world_book_version(book)
        session.flush()
        return _world_entry_to_response(entry)


def update_world_entry(world_book_id: str, entry_id: str, payload: WorldEntryUpdate) -> dict[str, Any]:
    with get_session() as session:
        book = session.get(WorldBook, world_book_id)
        if not book:
            raise ValueError("世界观不存在")
        entry = session.get(WorldEntry, entry_id)
        if not entry or entry.world_book_id != world_book_id:
            raise ValueError("世界观条目不存在")

        fields = _payload_to_world_entry_fields(payload)
        has_content_change = any(getattr(entry, key) != value for key, value in fields.items())
        for key, value in fields.items():
            setattr(entry, key, value)

        if has_content_change:
            entry.updated_at = _now()
            _bump_world_book_version(book)
        session.flush()
        return _world_entry_to_response(entry)


def disable_world_entry(world_book_id: str, entry_id: str) -> dict[str, Any]:
    return _set_world_entry_status(world_book_id, entry_id, "disabled")


def enable_world_entry(world_book_id: str, entry_id: str) -> dict[str, Any]:
    return _set_world_entry_status(world_book_id, entry_id, "active")


def _set_world_entry_status(world_book_id: str, entry_id: str, status: str) -> dict[str, Any]:
    with get_session() as session:
        book = session.get(WorldBook, world_book_id)
        if not book:
            raise ValueError("世界观不存在")
        entry = session.get(WorldEntry, entry_id)
        if not entry or entry.world_book_id != world_book_id:
            raise ValueError("世界观条目不存在")

        if entry.status != status:
            entry.status = status
            entry.updated_at = _now()
            _bump_world_book_version(book)
        session.flush()
        return _world_entry_to_response(entry)


def load_world_book_to_project(project_id: str, payload: ProjectWorldSnapshotCreate) -> dict[str, Any]:
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            raise ValueError("项目不存在")

        book = session.get(WorldBook, payload.source_world_book_id)
        if not book:
            raise ValueError("世界观不存在")
        if book.status != "active":
            raise ValueError("只有可加载状态的世界观可以加入项目")

        entries = session.scalars(
            select(WorldEntry)
            .where(WorldEntry.world_book_id == book.id, WorldEntry.status == "active")
            .order_by(WorldEntry.priority.desc(), WorldEntry.updated_at.desc())
        ).all()
        now = _now()
        entry_count, active_entry_count = _entry_counts(session, book.id)
        snapshot_content = json.dumps(
            _world_book_to_response(book, entry_count=entry_count, active_entry_count=active_entry_count),
            ensure_ascii=False,
        )
        entry_snapshot_content = json.dumps([_world_entry_to_response(entry) for entry in entries], ensure_ascii=False)

        if payload.load_mode == "replace":
            if not payload.replace_snapshot_id:
                raise ValueError("替换世界观时必须提供项目内世界观快照 ID")
            snapshot = session.get(ProjectWorldSnapshot, payload.replace_snapshot_id)
            if not snapshot or snapshot.project_id != project_id:
                raise ValueError("要替换的项目世界观不存在")

            snapshot.source_world_book_id = book.id
            snapshot.source_version = book.version
            snapshot.name = book.name
            snapshot.genre = book.genre
            snapshot.snapshot_content = snapshot_content
            snapshot.entry_snapshot_content = entry_snapshot_content
            snapshot.updated_at = now
        else:
            existing_snapshot = session.scalar(
                select(ProjectWorldSnapshot).where(
                    ProjectWorldSnapshot.project_id == project_id,
                    ProjectWorldSnapshot.name == book.name,
                )
            )
            if existing_snapshot:
                raise ValueError("世界观名称与项目中已有世界观重复，请选择替换已有世界观或修改名称")

            snapshot = ProjectWorldSnapshot(
                id=str(uuid4()),
                project_id=project_id,
                source_world_book_id=book.id,
                source_version=book.version,
                name=book.name,
                genre=book.genre,
                snapshot_content=snapshot_content,
                entry_snapshot_content=entry_snapshot_content,
                loaded_at=now,
                updated_at=now,
            )
            session.add(snapshot)

        session.flush()
        return _snapshot_to_response(snapshot)
