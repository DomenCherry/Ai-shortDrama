"""数据库连接模块，负责 SQLAlchemy engine、session 和表初始化。"""
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy 声明式模型基类。"""
    pass


@lru_cache
def get_engine():
    """创建数据库 engine，统一使用项目配置中的数据库连接串。"""
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory():
    """创建 SQLAlchemy session 工厂，供请求和 service 层复用。"""
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def initialize_database() -> None:
    """按当前模型创建缺失的数据表，主要服务本地开发启动。"""
    from app.models.db_models import (  # noqa: F401
        CharacterCard,
        EpisodeContentGenerationVersion,
        ModelApiConfig,
        ModelApiTestLog,
        Project,
        ProjectCharacterSnapshot,
        ProjectCopywriting,
        ProjectEpisodeContent,
        ProjectEpisodeOutline,
        ProjectEpisodeScript,
        ProjectEpisodeScriptVersion,
        ProjectScriptBlock,
        ProjectScriptCheckRun,
        ProjectScriptGeneration,
        ProjectScriptScene,
        ProjectStoryboardShot,
        ProjectStoryboard,
        ProjectShotPrompt,
        ProjectStoryOutline,
        ProjectWorldSnapshot,
        ReferenceStoryStructureDraft,
        WorldBook,
        WorldEntry,
    )

    Base.metadata.create_all(bind=get_engine())


@contextmanager
def get_session() -> Iterator[Session]:
    """提供带自动提交和回滚保护的数据库 session 上下文。"""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
