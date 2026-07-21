#!/usr/bin/env python3
"""
Shared result type returned by every parser.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseResult:
    source: Path
    parser: str          # "kreuzberg" | "docling" | "vlm"
    content: str         # full structured Markdown
    page_count: int | None = None
    extras: dict = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def save(self, output_dir: Path) -> Path:
        """Write content to <output_dir>/<stem>.txt, deduplicating if needed."""
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / (self.source.stem + ".txt")
        if out.exists():
            i = 1
            while out.exists():
                out = output_dir / f"{self.source.stem}_{i}.txt"
                i += 1
        out.write_text(self.content, encoding="utf-8")
        return out
