from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class UploadResponse(BaseModel):
    job_id: str
    status: Literal["queued"] = "queued"
    filename: str


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "done", "failed"]
    filename: str
    created_at: datetime
    updated_at: datetime
    error: str | None = None


class ResultResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    markdown: str
    summary: dict


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    redis: Literal["ok", "error"]
