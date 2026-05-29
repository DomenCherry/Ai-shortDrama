from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


ConfigType = Literal["text", "image"]


class ModelApiConfigCreate(BaseModel):
    config_type: ConfigType
    provider_name: str = Field(min_length=1)
    api_base_url: HttpUrl
    api_key: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    image_size: Optional[str] = None
    remark: Optional[str] = None
    enabled: bool = True


class ModelApiConfigResponse(BaseModel):
    id: str
    config_type: ConfigType
    provider_name: str
    api_base_url: str
    api_key_masked: str
    model_name: str
    image_size: Optional[str]
    remark: Optional[str]
    enabled: bool
    last_test_status: str
    last_tested_at: Optional[str]
    last_test_error: Optional[str]
    created_at: str
    updated_at: str


class ModelApiTestResponse(BaseModel):
    success: bool
    status: str
    message: str
    latency_ms: Optional[int] = None
    tested_at: str


class ProjectCreate(BaseModel):
    title: Optional[str] = None
    idea: str = Field(min_length=1)
    target_platform: Optional[str] = "抖音"
    genre: Optional[str] = None
    episode_count: int = 20
    episode_duration: float = 1
    target_audience: Optional[str] = None
    style: Optional[str] = None
    remark: Optional[str] = None

    @field_validator("episode_count")
    @classmethod
    def validate_episode_count(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("集数必须是大于 0 的整数")
        return value

    @field_validator("episode_duration")
    @classmethod
    def validate_episode_duration(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("单集时长必须大于 0 分钟")
        if value > 2:
            raise ValueError("单集时长不能超过 2 分钟")
        return value


class ProjectResponse(BaseModel):
    id: str
    title: str
    idea: str
    target_platform: Optional[str]
    genre: Optional[str]
    episode_count: int
    episode_duration: float
    total_duration: float
    target_audience: Optional[str]
    style: Optional[str]
    remark: Optional[str]
    status: str
    created_at: str
    updated_at: str

