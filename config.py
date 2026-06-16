#!/usr/bin/env python3
"""
Pipeline configuration — all tunables in one place.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# ── Recognised extensions by broad category ──────────────────────────────────

OFFICE_EXTENSIONS = frozenset({
    ".docx", ".doc", ".odt", ".rtf",
    ".xlsx", ".xls", ".ods",
    ".pptx", ".ppt", ".odp",
})

IMAGE_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg",
    ".tiff", ".tif", ".bmp", ".webp",
})


@dataclass
class Config:
    # ── Workspace ─────────────────────────────────────────────────────────────
    base_dir: Path = Path("/home/nullkuhl/docs")

    # ── PDF classification ────────────────────────────────────────────────────
    # > long_pdf_threshold pages → treated as "long" (sample head+tail only)
    long_pdf_threshold: int = 50
    # avg chars/page below this → classified as scanned
    scan_char_threshold: int = 50
    # how many evenly-spaced pages to sample for scanned detection
    scan_sample_pages: int = 5

    # ── Long PDF page sampling ────────────────────────────────────────────────
    long_head_pages: int = 10
    long_tail_pages: int = 10

    # ── VLM endpoint (OpenAI-compatible, e.g. vLLM) ───────────────────────────
    vlm_base_url: str = "http://197.46.212.11:8000/v1"
    vlm_model: str = "Qwen/Qwen3.6-27B-FP8"
    vlm_max_tokens: int = 8192
    vlm_image_dpi: int = 200        # render DPI for PDF → image conversion
    vlm_max_workers: int = 4        # parallel page requests to the VLM server
    vlm_retry_attempts: int = 3
    vlm_retry_backoff: float = 2.0  # seconds; doubles each retry

    # ── Directory helpers ─────────────────────────────────────────────────────
    @property
    def input_dir(self) -> Path:
        return self.base_dir / "input"

    @property
    def output_dir(self) -> Path:
        return self.base_dir / "output"

    @property
    def sorted_dir(self) -> Path:
        return self.base_dir / "sorted"

    @property
    def temp_dir(self) -> Path:
        return self.base_dir / "temp"

    def ensure_dirs(self) -> None:
        for path in [
            self.input_dir,
            self.output_dir,
            self.temp_dir,
            self.sorted_dir / "office",
            self.sorted_dir / "images",
            self.sorted_dir / "pdfs" / "short_text",
            self.sorted_dir / "pdfs" / "short_scanned",
            self.sorted_dir / "pdfs" / "long_text",
            self.sorted_dir / "pdfs" / "long_scanned",
        ]:
            path.mkdir(parents=True, exist_ok=True)
