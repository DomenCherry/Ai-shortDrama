"""核心配置模块，负责读取后端运行时环境配置。"""
from functools import lru_cache
from pydantic import BaseModel
import os

from dotenv import load_dotenv


class Settings(BaseModel):
    """后端运行配置，集中描述应用名称、跨域来源和数据库连接。"""
    app_name: str = "AI Short Drama API"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    asset_root: str = "workspace/assets"
    database_url: str = (
        "postgresql+psycopg://ai_short_drama:ai_short_drama@127.0.0.1:5432/ai_short_drama"
    )


@lru_cache
def get_settings() -> Settings:
    """读取并缓存应用配置，避免每次请求重复解析环境变量。"""
    load_dotenv()
    default_origins = ",".join(Settings().cors_origins)
    origins = os.getenv("API_CORS_ORIGINS", default_origins)
    return Settings(
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        database_url=os.getenv(
            "API_DATABASE_URL",
            "postgresql+psycopg://ai_short_drama:ai_short_drama@127.0.0.1:5432/ai_short_drama",
        ),
        asset_root=os.getenv("API_ASSET_ROOT", "workspace/assets"),
    )
