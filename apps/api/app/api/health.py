"""健康检查路由模块，用于确认后端服务是否可访问。"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
@router.get("/api/health")
def health_check() -> dict[str, str]:
    """返回服务健康状态，用于本地调试和部署探活。"""
    return {"status": "ok"}
