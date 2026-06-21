from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    # Per-job workspace — no default, must be set by the worker
    base_dir: Path

    # PDF classification thresholds
    vlm_text_threshold: int = 10
    long_pdf_threshold: int = 200
    scanned_long_threshold: int = 20
    scan_char_threshold: int = 50
    scan_sample_pages: int = 5

    # Long PDF page sampling
    long_head_pages: int = 10
    long_tail_pages: int = 10

    # VLM endpoint
    vlm_base_url: str = "http://197.46.212.11:8000/v1"
    vlm_model: str = "Qwen/Qwen3.6-27B-FP8"
    vlm_max_tokens: int = 8192
    vlm_image_dpi: int = 200
    vlm_max_workers: int = 4
    vlm_retry_attempts: int = 3
    vlm_retry_backoff: float = 2.0

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
            self.sorted_dir / "pdfs" / "vlm_text",
            self.sorted_dir / "pdfs" / "short_text",
            self.sorted_dir / "pdfs" / "short_scanned",
            self.sorted_dir / "pdfs" / "long_text",
            self.sorted_dir / "pdfs" / "long_scanned",
        ]:
            path.mkdir(parents=True, exist_ok=True)
