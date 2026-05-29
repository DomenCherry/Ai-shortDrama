from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


ConfigType = Literal["text", "image"]
ProviderMode = Literal["preset", "custom"]
CharacterGender = Literal["男", "女"]
CharacterCardStatus = Literal["draft", "active", "archived"]


class ModelApiConfigCreate(BaseModel):
    config_type: ConfigType
    provider_mode: ProviderMode = "custom"
    provider_preset: Optional[str] = None
    provider_name: Optional[str] = None
    api_base_url: Optional[str] = None
    api_key: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    image_size: Optional[str] = None
    endpoint_path: Optional[str] = None
    supports_reference_image: bool = False
    remark: Optional[str] = None
    enabled: bool = True

    @field_validator(
        "provider_preset",
        "provider_name",
        "api_base_url",
        "api_key",
        "model_name",
        "image_size",
        "endpoint_path",
        "remark",
        mode="before",
    )
    @classmethod
    def normalize_config_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ModelApiConfigResponse(BaseModel):
    id: str
    config_type: ConfigType
    provider_mode: ProviderMode
    provider_preset: Optional[str]
    provider_name: str
    api_base_url: str
    api_key_masked: str
    model_name: str
    image_size: Optional[str]
    endpoint_path: Optional[str]
    supports_reference_image: bool
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


class CharacterCardBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    gender: CharacterGender
    role_type: str = Field(min_length=1, max_length=40)
    identity: str = Field(min_length=1, max_length=200)
    background: Optional[str] = None
    personality: Optional[str] = None
    goal: str = Field(min_length=1)
    motivation: Optional[str] = None
    secret: Optional[str] = None
    conflict_points: Optional[str] = None
    relationship_notes: Optional[str] = None
    speech_style: Optional[str] = None
    catchphrases: Optional[str] = None
    emotional_arc: Optional[str] = None
    story_function: Optional[str] = None
    visual_description: Optional[str] = None
    image_keywords: Optional[str] = None
    reference_image_url: Optional[str] = None
    reference_local_path: Optional[str] = None
    turnaround_prompt: Optional[str] = None
    status: CharacterCardStatus = "draft"

    @field_validator(
        "name",
        "role_type",
        "identity",
        "background",
        "personality",
        "goal",
        "motivation",
        "secret",
        "conflict_points",
        "relationship_notes",
        "speech_style",
        "catchphrases",
        "emotional_arc",
        "story_function",
        "visual_description",
        "image_keywords",
        "reference_image_url",
        "reference_local_path",
        "turnaround_prompt",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("性别不能为空")
        gender = value.strip()
        if gender not in {"男", "女"}:
            raise ValueError("性别只能选择男或女")
        return gender


class CharacterCardCreate(CharacterCardBase):
    pass


class CharacterCardUpdate(CharacterCardBase):
    pass


class CharacterCardResponse(CharacterCardBase):
    id: str
    version: int
    turnaround_image_url: Optional[str] = None
    turnaround_local_path: Optional[str] = None
    turnaround_generation_prompt: Optional[str] = None
    turnaround_status: str = "none"
    turnaround_version: int = 0
    turnaround_confirmed_at: Optional[str] = None
    created_at: str
    updated_at: str


class CharacterReferenceImageUpload(BaseModel):
    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    data_url: str = Field(min_length=1)


class CharacterImageAssetResponse(BaseModel):
    character_card_id: str
    image_url: str
    local_path: str
    updated_at: str


class CharacterTurnaroundGenerate(BaseModel):
    prompt: Optional[str] = None


class CharacterTurnaroundResponse(BaseModel):
    character_card_id: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    generation_prompt: Optional[str] = None
    status: str
    version: int
    confirmed_at: Optional[str] = None
    updated_at: str


class ProjectCharacterSnapshotCreate(BaseModel):
    source_character_card_id: str = Field(min_length=1)
    load_mode: Literal["new", "replace"] = "new"
    replace_snapshot_id: Optional[str] = None


class ProjectCharacterSnapshotResponse(BaseModel):
    id: str
    project_id: str
    source_character_card_id: str
    source_version: int
    name: str
    gender: CharacterGender
    role_type: str
    snapshot_content: str
    visual_description: Optional[str]
    reference_image_url: Optional[str]
    reference_local_path: Optional[str]
    loaded_at: str
    updated_at: str
