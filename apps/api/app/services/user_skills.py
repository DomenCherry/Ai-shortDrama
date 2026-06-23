"""用户侧业务 Skill 管理服务，负责扫描仓库 skills 目录并保存全局开关。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.db import get_session
from app.models.db_models import UserSkillSetting
from app.models.schemas import UserSkillUpdate


@dataclass(frozen=True)
class SkillDefinition:
    """仓库内用户侧业务 Skill 的静态定义。"""

    name: str
    description: str
    source_dir: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def skills_root() -> Path:
    """定位仓库根目录下的用户侧业务 skills 目录。"""
    return Path(__file__).resolve().parents[4] / "skills"


def _parse_frontmatter(text: str) -> dict[str, str]:
    """解析 SKILL.md 顶部简单 YAML frontmatter，仅读取一层字符串字段。"""
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}
    lines = stripped.splitlines()
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def discover_user_skills() -> list[SkillDefinition]:
    """扫描 skills/*/SKILL.md，返回可管理的用户侧业务 Skill 定义。"""
    root = skills_root()
    if not root.exists():
        return []

    definitions: list[SkillDefinition] = []
    for path in sorted(root.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(text)
        name = frontmatter.get("name") or path.parent.name
        definitions.append(
            SkillDefinition(
                name=name,
                description=frontmatter.get("description") or "",
                source_dir=f"skills/{path.parent.name}",
            )
        )
    return definitions


def _definition_by_name(skill_name: str) -> SkillDefinition:
    definition = next((item for item in discover_user_skills() if item.name == skill_name), None)
    if definition is None:
        raise ValueError("Skill 不存在")
    return definition


def _skill_to_response(definition: SkillDefinition, setting: UserSkillSetting | None = None) -> dict[str, Any]:
    return {
        "name": definition.name,
        "description": definition.description,
        "source_dir": definition.source_dir,
        "enabled": setting.enabled if setting else True,
        "updated_at": setting.updated_at.isoformat() if setting else None,
    }


def list_user_skills() -> list[dict[str, Any]]:
    """列出用户侧业务 Skill。未保存开关的 Skill 默认启用。"""
    definitions = discover_user_skills()
    with get_session() as session:
        settings = {
            setting.skill_name: setting
            for setting in session.scalars(select(UserSkillSetting)).all()
        }
        return [_skill_to_response(definition, settings.get(definition.name)) for definition in definitions]


def update_user_skill(skill_name: str, payload: UserSkillUpdate) -> dict[str, Any]:
    """创建或更新指定用户侧业务 Skill 的全局开关。"""
    definition = _definition_by_name(skill_name)
    current_time = _now()

    with get_session() as session:
        setting = session.get(UserSkillSetting, skill_name)
        if setting is None:
            setting = UserSkillSetting(
                skill_name=skill_name,
                enabled=payload.enabled,
                created_at=current_time,
                updated_at=current_time,
            )
            session.add(setting)
        else:
            setting.enabled = payload.enabled
            setting.updated_at = current_time
        session.flush()
        return _skill_to_response(definition, setting)


def is_user_skill_enabled(skill_name: str) -> bool:
    """读取指定用户侧业务 Skill 开关；存在定义但无设置时默认启用。"""
    _definition_by_name(skill_name)
    with get_session() as session:
        setting = session.get(UserSkillSetting, skill_name)
        return setting.enabled if setting else True


def ensure_user_skill_enabled(skill_name: str) -> None:
    """生成任务入口使用的强校验，禁用时阻断模型调用。"""
    if not is_user_skill_enabled(skill_name):
        raise ValueError(f"{skill_name} skill 已禁用，请在 Skill 管理中启用后再使用生成能力。")
