#!/usr/bin/env python3
"""Shared result type returned by every parser script."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseResult:
    source: Path
    parser: str
    content: str
    page_count: int | None = None
    extras: dict = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def save(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / (self.source.stem + ".txt")
        if out.exists():
            i = 1
            while out.exists():
                out = output_dir / f"{self.source.stem}_{i}.txt"
                i += 1
        out.write_text(self.content, encoding="utf-8")
        return out

    def emit(self) -> None:
        """Print a single JSON line to stdout — read by the orchestrator."""
        print(json.dumps({
            "ok":           self.ok,
            "parser":       self.parser,
            "pages":        self.page_count,
            "error":        self.error,
            "table_count":  self.extras.get("table_count"),
            "cpu_fallback": self.extras.get("cpu_fallback", False),
        }, ensure_ascii=False))
        sys.stdout.flush()
