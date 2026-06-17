#!/usr/bin/env python3
"""
Main pipeline orchestrator.

Routing table:
  OFFICE          → Kreuzberg  (DOCX / XLSX / PPTX)
  IMAGE           → VLM        (PNG / JPG / …)
  PDF_SHORT_TEXT  → Docling    (full file)
  PDF_SHORT_SCAN  → VLM        (full file)
  PDF_LONG_TEXT   → Docling    (first 10 + last 10 pages extracted to temp)
  PDF_LONG_SCAN   → VLM        (first 10 + last 10 pages extracted to temp)

All routes produce a .md file in output/ with YAML front-matter + full content.
A JSON summary of all results is written to output/_summary.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

from config import Config
from detector import DocClass, classify, extract_pdf_pages
from parsers import ParseResult


# ── Parser imports (lazy — avoid loading heavy models until actually needed) ──

def _get_office_parse() -> Callable:
    from parsers.office import parse
    return parse


def _get_docling_parse() -> Callable:
    from parsers.docling_parser import parse
    return parse


def _get_vlm_parse(cfg: Config) -> Callable:
    from parsers.vlm_parser import parse as _parse
    return lambda path: _parse(path, cfg)


# ── Per-file processing ───────────────────────────────────────────────────────

def _process_file(
    path: Path,
    cls: DocClass,
    cfg: Config,
    output_dir: Path,
) -> ParseResult:
    """Route one file through the appropriate parser and save its output."""

    t0 = time.time()

    if cls == DocClass.OFFICE:
        result = _get_office_parse()(path)

    elif cls in (DocClass.IMAGE, DocClass.PDF_VLM_TEXT, DocClass.PDF_SHORT_SCAN):
        result = _get_vlm_parse(cfg)(path)

    elif cls == DocClass.PDF_SHORT_TEXT:
        result = _get_docling_parse()(path)

    elif cls in (DocClass.PDF_LONG_TEXT, DocClass.PDF_LONG_SCAN):
        # Extract first N + last N pages → temp PDF, then parse that
        tmp = cfg.temp_dir / f"_sample_{path.stem}.pdf"
        n_extracted = extract_pdf_pages(
            path, tmp,
            head=cfg.long_head_pages,
            tail=cfg.long_tail_pages,
        )
        print(
            f"    [pipeline] extracted {n_extracted} pages "
            f"(head {cfg.long_head_pages} + tail {cfg.long_tail_pages}) → {tmp.name}"
        )

        result = _get_vlm_parse(cfg)(tmp)

        # Overwrite source so the output filename matches the original
        result.source = path
        tmp.unlink(missing_ok=True)

    elif cls == DocClass.UNKNOWN:
        print(f"    [pipeline] WARNING: could not determine page count for {path.name} — skipping (encrypted or corrupted)")
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
        print(f"    ✓  {path.name}  →  {out.name}  ({elapsed:.1f}s)")
    else:
        print(f"    ✗  {path.name}  ERROR: {result.error}")

    result.extras["elapsed_s"] = round(elapsed, 2)
    return result


# ── Main entry point ──────────────────────────────────────────────────────────

def run(
    cfg: Config,
    *,
    sort_first: bool = True,
    input_paths: list[Path] | None = None,
) -> list[ParseResult]:
    """
    Run the full pipeline.

    Args:
        cfg:          pipeline configuration
        sort_first:   when True, move files from input/ to sorted/ first
        input_paths:  if provided, process these specific paths directly
                      (bypasses sorting; files must already be in sorted/)
    """
    cfg.ensure_dirs()
    run_start = time.time()

    # ── 1. Sort input files ───────────────────────────────────────────────────
    if input_paths is None:
        if sort_first:
            from sorter import sort_input
            print("\n── Sorting input files ──────────────────────────────────")
            sorted_map = sort_input(cfg)
            paths = [p for paths in sorted_map.values() for p in paths]
        else:
            # Collect everything already in sorted/
            paths = [
                f
                for f in cfg.sorted_dir.rglob("*")
                if f.is_file() and not f.name.startswith("_")
            ]
    else:
        paths = input_paths

    if not paths:
        print("  [pipeline] no files to process")
        return []

    # ── 2. Process each file ──────────────────────────────────────────────────
    print(f"\n── Processing {len(paths)} file(s) ─────────────────────────────")
    results: list[ParseResult] = []

    for path in sorted(paths):
        cls = classify(path, cfg)
        print(f"\n  [{cls.name:18s}]  {path.name}")
        result = _process_file(path, cls, cfg, cfg.output_dir)
        results.append(result)

    # ── 3. Write summary ──────────────────────────────────────────────────────
    summary = []
    ok_count = err_count = 0
    for r in results:
        entry = {
            "source":     r.source.name,
            "parser":     r.parser,
            "pages":      r.page_count,
            "ok":         r.ok,
            "error":      r.error,
            "elapsed_s":  r.extras.get("elapsed_s"),
            "table_count": r.extras.get("table_count"),
        }
        summary.append(entry)
        if r.ok:
            ok_count += 1
        else:
            err_count += 1

    total_elapsed = time.time() - run_start
    minutes, seconds = divmod(total_elapsed, 60)
    elapsed_str = f"{int(minutes)}m {seconds:.1f}s" if minutes else f"{seconds:.1f}s"

    summary_path = cfg.output_dir / "_summary.json"
    summary_data = {
        "total_elapsed_s": round(total_elapsed, 2),
        "files": summary,
    }
    summary_path.write_text(json.dumps(summary_data, ensure_ascii=False, indent=2), encoding="utf-8")

    total = len(results)
    print(
        f"\n── Done — {ok_count}/{total} succeeded, {err_count} errors  "
        f"[total: {elapsed_str}]\n"
        f"   Output:  {cfg.output_dir}\n"
        f"   Summary: {summary_path}\n"
    )
    return results
