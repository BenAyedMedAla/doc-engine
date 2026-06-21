from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    max_upload_size_mb: int = 100

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Worker
    workspace_root: Path = Path("/workspace")
    job_ttl: int = 86400  # seconds — Redis keys expire after this

    # VLM endpoint
    vlm_base_url: str = "http://197.46.212.11:8000/v1"
    vlm_model: str = "Qwen/Qwen3.6-27B-FP8"
    vlm_max_tokens: int = 8192
    vlm_image_dpi: int = 200
    vlm_max_workers: int = 4
    vlm_retry_attempts: int = 3
    vlm_retry_backoff: float = 2.0

    # PDF classification thresholds
    vlm_text_threshold: int = 10
    long_pdf_threshold: int = 200
    scanned_long_threshold: int = 20
    scan_char_threshold: int = 50
    scan_sample_pages: int = 5
    long_head_pages: int = 10
    long_tail_pages: int = 10


settings = Settings()
