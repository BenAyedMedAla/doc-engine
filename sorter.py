#!/usr/bin/env python3
"""
Sort every file in input/ into its appropriate sorted/ subfolder.

Classification is per-file: page count + text-layer sampling for PDFs,
extension matching for Office docs and images.  No file content is parsed
beyond what detector.py reads (XRef metadata + sampled text layer).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from config import Config
from detector import DocClass, classify

# Maps each class to its sorted/ subdirectory path components
_CLASS_SUBDIR: dict[DocClass, tuple[str, ...]] = {
    DocClass.OFFICE:         ("office",),
    DocClass.IMAGE:          ("images",),
    DocClass.PDF_SHORT_TEXT: ("pdfs", "short_text"),
    DocClass.PDF_SHORT_SCAN: ("pdfs", "short_scanned"),
    DocClass.PDF_LONG_TEXT:  ("pdfs", "long_text"),
    DocClass.PDF_LONG_SCAN:  ("pdfs", "long_scanned"),
}


def _unique_dest(dest: Path) -> Path:
    """Return `dest`, appending _1, _2, … if a file already exists there."""
    if not dest.exists():
        return dest
    stem, suf = dest.stem, dest.suffix
    i = 1
    while True:
        candidate = dest.with_name(f"{stem}_{i}{suf}")
        if not candidate.exists():
            return candidate
        i += 1


def sort_input(cfg: Config) -> dict[DocClass, list[Path]]:
    """
    Move every file from input/ to its sorted subfolder.
    Returns a mapping  DocClass → [sorted file paths]  for downstream use.
    Already-sorted files (absent from input/) are not touched.
    """
    cfg.ensure_dirs()
    result: dict[DocClass, list[Path]] = {cls: [] for cls in DocClass}

    files = [f for f in sorted(cfg.input_dir.iterdir()) if f.is_file()]
    if not files:
        print("  [sorter] input/ is empty — nothing to sort")
        return result

    for src in files:
        cls = classify(src, cfg)
        if cls == DocClass.UNKNOWN:
            print(f"  [skip]   {src.name}  (unrecognised extension)")
            continue

        dest_dir = cfg.sorted_dir.joinpath(*_CLASS_SUBDIR[cls])
        dest     = _unique_dest(dest_dir / src.name)
        shutil.move(str(src), str(dest))
        result[cls].append(dest)

        tag = cls.name.replace("PDF_", "").replace("_", "/").lower()
        print(f"  [{tag:18s}]  {src.name}")

    return result
