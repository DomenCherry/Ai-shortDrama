from fastapi import APIRouter

from app.api.project_routes import (
    assets,
    episode_contents,
    episode_outlines,
    episode_scripts,
    management,
    production,
    story_outline,
)

router = APIRouter()

router.include_router(management.router, prefix="/api/projects", tags=["projects"])
router.include_router(assets.router, prefix="/api/projects", tags=["projects"])
router.include_router(story_outline.router, prefix="/api/projects", tags=["projects"])
router.include_router(episode_outlines.router, prefix="/api/projects", tags=["projects"])
router.include_router(episode_contents.router, prefix="/api/projects", tags=["projects"])
router.include_router(episode_scripts.router, prefix="/api/projects", tags=["projects"])
router.include_router(production.router, prefix="/api/projects", tags=["projects"])
