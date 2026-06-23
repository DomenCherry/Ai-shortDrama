"""FastAPI 应用启动模块，负责装配中间件、路由和数据库初始化。"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.character_cards import router as character_cards_router
from app.api.health import router as health_router
from app.api.model_configs import router as model_configs_router
from app.api.projects import router as projects_router
from app.api.skills import router as skills_router
from app.api.world_books import router as world_books_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例，并挂载中间件、路由和数据库初始化事件。"""
    settings = get_settings()

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(character_cards_router)
    app.include_router(model_configs_router)
    app.include_router(projects_router)
    app.include_router(skills_router)
    app.include_router(world_books_router)

    asset_root = Path(settings.asset_root)
    asset_root.mkdir(parents=True, exist_ok=True)
    app.mount("/api/assets", StaticFiles(directory=asset_root), name="assets")
    return app


app = create_app()
