"""用户侧业务 Skill 路由模块，提供列表和全局开关管理。"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import UserSkillResponse, UserSkillUpdate
from app.services import user_skills

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=list[UserSkillResponse])
def list_user_skills() -> list[dict]:
    """读取仓库内可供用户使用的业务 Skill 及其启用状态。"""
    return user_skills.list_user_skills()


@router.patch("/{skill_name}", response_model=UserSkillResponse)
def update_user_skill(skill_name: str, payload: UserSkillUpdate) -> dict:
    """切换指定用户侧业务 Skill 的全局启用状态。"""
    try:
        return user_skills.update_user_skill(skill_name, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
