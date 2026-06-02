from functools import lru_cache
from pydantic import BaseModel
import os

from dotenv import load_dotenv


class Settings(BaseModel):
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
