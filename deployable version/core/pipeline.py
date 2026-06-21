from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Callable

from .config import Config
from .detector import DocClass, classify, extract_pdf_pages
from .parsers import ParseResult

logger = logging.getLogger(__name__)


def _get_office_parse() -> Callable:
    from .parsers.office import parse
    return parse


def _get_docling_parse() -> Callable:
    from .parsers.docling_parser import parse
    return parse


def _get_vlm_parse(cfg: Config) -> Callable:
    from .parsers.vlm_parser import parse as _parse
    return lambda path: _parse(path, cfg)


def _process_file(path: Path, cls: DocClass, cfg: Config, output_dir: Path) -> ParseResult:
    t0 = time.time()

    if cls == DocClass.OFFICE:
        result = _get_office_parse()(path)

    elif cls in (DocClass.IMAGE, DocClass.PDF_VLM_TEXT, DocClass.PDF_SHORT_SCAN):
        result = _get_vlm_parse(cfg)(path)

    elif cls == DocClass.PDF_SHORT_TEXT:
        result = _get_docling_parse()(path)

    elif cls in (DocClass.PDF_LONG_TEXT, DocClass.PDF_LONG_SCAN):
        tmp = cfg.temp_dir / f"_sample_{path.stem}.pdf"
        n_extracted = extract_pdf_pages(
            path, tmp,
            head=cfg.long_head_pages,
            tail=cfg.long_tail_pages,
        )
        logger.info(
            "Extracted %d pages (head %d + tail %d) from %s",
            n_extracted, cfg.long_head_pages, cfg.long_tail_pages, path.name,
        )
        result = _get_vlm_parse(cfg)(tmp)
        result.source = path
        tmp.unlink(missing_ok=True)

    elif cls == DocClass.UNKNOWN:
        logger.warning("Skipping unreadable file: %s", path.name)
        return ParseResult(
            source=path, parser="none", content="",
            error="unreadable PDF: page count is 0 after all fallbacks (encrypted or corrupted)",
        )

    else:
        return ParseResult(
            source=path, parser="none", content="",
            error=f"unhandled class {cls}",
        )

    elapsed = time.time() - t0
    if result.ok:
        out = result.save(output_dir)
        logger.info("Parsed %s → %s (%.1fs)", path.name, out.name, elapsed)
    else:
        logger.error("Parse failed for %s: %s", path.name, result.error)

    result.extras["elapsed_s"] = round(elapsed, 2)
    return result


def run(
    cfg: Config,
    *,
    sort_first: bool = True,
    input_paths: list[Path] | None = None,
) -> list[ParseResult]:
    cfg.ensure_dirs()
    run_start = time.time()

    if input_paths is None:
        if sort_first:
            from .sorter import sort_input
            logger.info("Sorting input files")
            sorted_map = sort_input(cfg)
            paths = [p for paths in sorted_map.values() for p in paths]
        else:
            paths = [
                f for f in cfg.sorted_dir.rglob("*")
                if f.is_file() and not f.name.startswith("_")
            ]
    else:
        paths = input_paths

    if not paths:
        logger.info("No files to process")
        return []

    logger.info("Processing %d file(s)", len(paths))
    results: list[ParseResult] = []

    for path in sorted(paths):
        cls = classify(path, cfg)
        logger.info("Routing [%s] %s", cls.name, path.name)
        result = _process_file(path, cls, cfg, cfg.output_dir)
        results.append(result)

    ok_count = sum(1 for r in results if r.ok)
    err_count = len(results) - ok_count
    total_elapsed = time.time() - run_start

    summary = [
        {
            "source":      r.source.name,
            "parser":      r.parser,
            "pages":       r.page_count,
            "ok":          r.ok,
            "error":       r.error,
            "elapsed_s":   r.extras.get("elapsed_s"),
            "table_count": r.extras.get("table_count"),
        }
        for r in results
    ]
    summary_path = cfg.output_dir / "_summary.json"
    summary_path.write_text(
        json.dumps({"total_elapsed_s": round(total_elapsed, 2), "files": summary},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(
        "Done — %d/%d succeeded, %d errors (%.1fs total)",
        ok_count, len(results), err_count, total_elapsed,
    )
    return results
