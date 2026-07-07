#!/usr/bin/env python3
"""
Recursively process every unique file under docs/input/EVIDENCE, regardless
of nesting depth. Bypasses the sorter (which only scans input/ non-recursively)
by calling pipeline.run() with an explicit input_paths list. Originals are
never moved. Files with identical content (same evidence reused across
multiple controls) are only passed to the engine once. Output is flat in
<base_dir>/output/.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from config import Config
from pipeline import run

EVIDENCE_ROOT = Path("/home/nullkuhl/docs/input/EVIDENCE")


def _hash(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    cfg = Config()
    cfg.vlm_model = "qwen3.6-27b-awq"  # actual model id served at cfg.vlm_base_url
    cfg.ensure_dirs()

    all_files = sorted(
        p for p in EVIDENCE_ROOT.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
    )

    seen: set[str] = set()
    files: list[Path] = []
    for p in all_files:
        h = _hash(p)
        if h in seen:
            continue
        seen.add(h)
        files.append(p)

    print(f"Found {len(all_files)} files under {EVIDENCE_ROOT}, "
          f"{len(files)} unique by content — processing unique set only")

    run(cfg, sort_first=False, input_paths=files)


if __name__ == "__main__":
    main()
