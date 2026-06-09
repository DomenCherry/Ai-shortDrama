"""项目服务兼容入口。

项目业务已经按领域拆分到 app.services.project 下。
本模块保留旧的公开函数名，避免路由和其他 service 在重构期间被迫同步改动。
"""

from app.services.project.assets import (
    delete_project_character_snapshot,
    delete_project_world_snapshot,
    list_project_character_snapshots,
    list_project_world_snapshots,
    update_project_character_snapshot,
    update_project_world_snapshot,
)
from app.services.project.common import mark_project_downstream_for_review as _mark_project_downstream_for_review
from app.services.project.management import create_project, get_project, list_projects, update_project
from app.services.project.production.copywriting import get_copywriting, upsert_copywriting
from app.services.project.production.storyboard import (
    create_storyboard_shot,
    delete_storyboard_shot,
    list_storyboard_shots,
    update_storyboard_shot,
)
from app.services.project.story.episode_contents import get_episode_content, upsert_episode_content
from app.services.project.story.episode_outlines import list_episode_outlines, upsert_episode_outline
from app.services.project.story.episode_scripts import get_episode_script, upsert_episode_script
from app.services.project.story.outline import (
    apply_reference_story_structure_draft,
    assist_story_outline,
    discard_reference_story_structure_draft,
    extract_reference_story_structure,
    generate_story_outline,
    get_reference_story_structure_draft,
    get_story_outline,
    list_reference_story_structure_drafts,
    rewrite_story_outline,
    upsert_story_outline,
)

__all__ = [
    "apply_reference_story_structure_draft",
    "assist_story_outline",
    "create_project",
    "create_storyboard_shot",
    "delete_project_character_snapshot",
    "delete_project_world_snapshot",
    "delete_storyboard_shot",
    "discard_reference_story_structure_draft",
    "extract_reference_story_structure",
    "generate_story_outline",
    "get_copywriting",
    "get_episode_content",
    "get_episode_script",
    "get_project",
    "get_reference_story_structure_draft",
    "get_story_outline",
    "list_episode_outlines",
    "list_project_character_snapshots",
    "list_project_world_snapshots",
    "list_projects",
    "list_reference_story_structure_drafts",
    "list_storyboard_shots",
    "rewrite_story_outline",
    "update_project",
    "update_project_character_snapshot",
    "update_project_world_snapshot",
    "update_storyboard_shot",
    "upsert_copywriting",
    "upsert_episode_content",
    "upsert_episode_outline",
    "upsert_episode_script",
    "upsert_story_outline",
    "_mark_project_downstream_for_review",
]
