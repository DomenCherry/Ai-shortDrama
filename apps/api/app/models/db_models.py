from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ModelApiConfig(Base):
    __tablename__ = "model_api_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    config_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    api_base_url: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_secret: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(160), nullable=False)
    image_size: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_test_status: Mapped[str] = mapped_column(String(24), nullable=False, default="untested")
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModelApiTestLog(Base):
    __tablename__ = "model_api_test_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    config_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("model_api_configs.id"), nullable=False, index=True
    )
    config_type: Mapped[str] = mapped_column(String(16), nullable=False)
    request_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    idea: Mapped[str] = mapped_column(Text, nullable=False)
    target_platform: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    episode_count: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_duration: Mapped[float] = mapped_column(Float, nullable=False)
    total_duration: Mapped[float] = mapped_column(Float, nullable=False)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    style: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
