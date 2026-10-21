"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreatedResponse(BaseModel):
    job_id: str
    status: JobStatus
    files_received: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    files: list[str] = Field(default_factory=list)
    stats: dict | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class ErrorResponse(BaseModel):
    detail: str


class PreviewResponse(BaseModel):
    job_id: str
    cleaned: list[dict] = Field(default_factory=list)
    rejected: list[dict] = Field(default_factory=list)
    cleaned_total: int = 0
    rejected_total: int = 0
