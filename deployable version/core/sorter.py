from __future__ import annotations

import logging
import shutil
from pathlib import Path

from .config import Config
from .detector import DocClass, classify

logger = logging.getLogger(__name__)

_CLASS_SUBDIR: dict[DocClass, tuple[str, ...]] = {
    DocClass.OFFICE:         ("office",),
    DocClass.IMAGE:          ("images",),
    DocClass.PDF_VLM_TEXT:   ("pdfs", "vlm_text"),
    DocClass.PDF_SHORT_TEXT: ("pdfs", "short_text"),
    DocClass.PDF_SHORT_SCAN: ("pdfs", "short_scanned"),
    DocClass.PDF_LONG_TEXT:  ("pdfs", "long_text"),
    DocClass.PDF_LONG_SCAN:  ("pdfs", "long_scanned"),
}


def _unique_dest(dest: Path) -> Path:
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
    cfg.ensure_dirs()
    result: dict[DocClass, list[Path]] = {cls: [] for cls in DocClass}

    files = [f for f in sorted(cfg.input_dir.iterdir()) if f.is_file()]
    if not files:
        logger.info("input/ is empty — nothing to sort")
        return result

    for src in files:
        cls = classify(src, cfg)
        if cls == DocClass.UNKNOWN:
            logger.warning("Skipping unrecognised or unreadable file: %s", src.name)
            continue
        dest_dir = cfg.sorted_dir.joinpath(*_CLASS_SUBDIR[cls])
        dest     = _unique_dest(dest_dir / src.name)
        shutil.move(str(src), str(dest))
        result[cls].append(dest)
        logger.info("Sorted [%s] %s", cls.name, src.name)

    return result
