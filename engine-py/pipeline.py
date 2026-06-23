#!/usr/bin/env python3
"""
Main pipeline orchestrator — subprocess model.

Each parser runs as an isolated subprocess with its own Python interpreter,
completely bypassing the GIL. This mirrors what the Rust orchestrator does
and gives true parallelism for all parser types.

Concurrency (same limits as the Rust orchestrator):
  - Office  : 8 concurrent  (CPU-only, sub-second)
  - Docling : 1 concurrent  (GPU-bound — 2+ causes VRAM OOM)
  - VLM     : 4 concurrent  (I/O-bound, network to vLLM server)

Parser scripts are reused from py-rs-version/parsers/.
pypdfium2 (classification + long-PDF extraction) stays in the main thread
because the C library is not thread-safe.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from config import Config
from detector import DocClass, classify, extract_pdf_pages
from parsers import ParseResult

# ── Concurrency gates ─────────────────────────────────────────────────────────

_OFFICE_SLOTS  = threading.Semaphore(8)
_DOCLING_SLOTS = threading.Semaphore(1)
_VLM_SLOTS     = threading.Semaphore(4)

# ── Parser script locations ───────────────────────────────────────────────────

_PARSERS_DIR = Path(__file__).parent.parent / "py-rs-version" / "parsers"

_SCRIPT: dict[DocClass, str] = {
    DocClass.OFFICE:        "office_parser.py",
    DocClass.PDF_SHORT_TEXT: "docling_parser.py",
}
# All other classes → vlm_parser.py


def _semaphore_for(cls: DocClass) -> threading.Semaphore:
    if cls == DocClass.OFFICE:
        return _OFFICE_SLOTS
    if cls == DocClass.PDF_SHORT_TEXT:
        return _DOCLING_SLOTS
    return _VLM_SLOTS


def _script_for(cls: DocClass) -> Path:
    return _PARSERS_DIR / _SCRIPT.get(cls, "vlm_parser.py")


def _vlm_extra(cfg: Config) -> list[str]:
    return [
        "--vlm-url",     cfg.vlm_base_url,
        "--vlm-model",   cfg.vlm_model,
        "--vlm-tokens",  str(cfg.vlm_max_tokens),
        "--vlm-dpi",     str(cfg.vlm_image_dpi),
        "--vlm-workers", str(cfg.vlm_max_workers),
        "--vlm-retries", str(cfg.vlm_retry_attempts),
        "--vlm-backoff", str(cfg.vlm_retry_backoff),
    ]


# ── Per-file subprocess call ──────────────────────────────────────────────────

def _process_file(
    parse_path: Path,    # actual file to parse (may be a temp for long PDFs)
    cls: DocClass,
    original_path: Path, # used for display and output filename
    cfg: Config,
) -> ParseResult:
    t0 = time.time()

    extra = _vlm_extra(cfg) if cls not in (DocClass.OFFICE, DocClass.PDF_SHORT_TEXT) else []
    cmd   = [
        sys.executable, str(_script_for(cls)),
        "--input",      str(parse_path),
        "--output-dir", str(cfg.output_dir),
    ] + extra

    proc    = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)

    # Parser scripts print one JSON line as the last line of stdout
    json_data: dict = {}
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                json_data = json.loads(line)
                break
            except json.JSONDecodeError:
                pass

    ok    = json_data.get("ok", False) and proc.returncode == 0
    error = (json_data.get("error") or None) if ok else (
        json_data.get("error") or f"process exited {proc.returncode}"
    )

    result = ParseResult(
        source=original_path,
        parser=json_data.get("parser", "unknown"),
        content="",           # subprocess already wrote the .md file
        page_count=json_data.get("pages"),
        extras={
            "elapsed_s":   round(elapsed, 2),
            "table_count": json_data.get("table_count"),
        },
        error=error,
    )

    if result.ok:
        print(f"    ✓  {original_path.name}  →  {original_path.stem}.md  ({elapsed:.1f}s)")
    else:
        print(f"    ✗  {original_path.name}  ERROR: {result.error}")

    return result


# ── Main entry point ──────────────────────────────────────────────────────────

def run(
    cfg: Config,
    *,
    sort_first: bool = True,
    input_paths: list[Path] | None = None,
) -> list[ParseResult]:
    cfg.ensure_dirs()
    run_start = time.time()

    # ── 1. Sort ───────────────────────────────────────────────────────────────
    if input_paths is None:
        if sort_first:
            from sorter import sort_input
            print("\n── Sorting input files ──────────────────────────────────")
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
        print("  [pipeline] no files to process")
        return []

    # ── 2. Classify + prepare long PDFs ──────────────────────────────────────
    # Both steps stay in the main thread — pypdfium2 is not thread-safe.
    print(f"\n── Processing {len(paths)} file(s) ─────────────────────────────")
    prepared: list[tuple[Path, DocClass, Path]] = []  # (parse_path, cls, original_path)

    for path in sorted(paths):
        cls = classify(path, cfg)
        print(f"  [{cls.name:18s}]  {path.name}")

        if cls in (DocClass.PDF_LONG_TEXT, DocClass.PDF_LONG_SCAN):
            tmp = cfg.temp_dir / f"_sample_{path.stem}.pdf"
            n   = extract_pdf_pages(path, tmp,
                                    head=cfg.long_head_pages,
                                    tail=cfg.long_tail_pages)
            print(f"    [pipeline] extracted {n} pages "
                  f"(head {cfg.long_head_pages} + tail {cfg.long_tail_pages}) → {tmp.name}")
            prepared.append((tmp, cls, path))

        elif cls == DocClass.UNKNOWN:
            print(f"    [pipeline] WARNING: unreadable — skipping {path.name}")
            prepared.append((path, cls, path))

        else:
            prepared.append((path, cls, path))

    # ── 3. Dispatch parsers concurrently ─────────────────────────────────────
    # Each subprocess has its own Python interpreter — no shared GIL.
    results: list[ParseResult] = []

    def _dispatch(parse_path: Path, cls: DocClass, original_path: Path) -> ParseResult:
        if cls == DocClass.UNKNOWN:
            return ParseResult(
                source=original_path, parser="none", content="",
                error="unreadable PDF (encrypted or corrupted)",
            )
        with _semaphore_for(cls):
            result = _process_file(parse_path, cls, original_path, cfg)
        if parse_path != original_path:
            parse_path.unlink(missing_ok=True)
        return result

    # 13 threads: enough to saturate all semaphore slots simultaneously
    with ThreadPoolExecutor(max_workers=13) as pool:
        futures = {
            pool.submit(_dispatch, pp, cls, op): op
            for pp, cls, op in prepared
        }
        for future in as_completed(futures):
            results.append(future.result())

    # ── 4. Write summary ──────────────────────────────────────────────────────
    summary = []
    ok_count = err_count = 0
    for r in results:
        summary.append({
            "source":      r.source.name,
            "parser":      r.parser,
            "pages":       r.page_count,
            "ok":          r.ok,
            "error":       r.error,
            "elapsed_s":   r.extras.get("elapsed_s"),
            "table_count": r.extras.get("table_count"),
        })
        if r.ok:
            ok_count += 1
        else:
            err_count += 1

    total_elapsed = time.time() - run_start
    minutes, seconds = divmod(total_elapsed, 60)
    elapsed_str = f"{int(minutes)}m {seconds:.1f}s" if minutes else f"{seconds:.1f}s"

    summary_path = cfg.output_dir / "_summary.json"
    summary_path.write_text(
        json.dumps(
            {"total_elapsed_s": round(total_elapsed, 2), "files": summary},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    total = len(results)
    print(
        f"\n── Done — {ok_count}/{total} succeeded, {err_count} errors  "
        f"[total: {elapsed_str}]\n"
        f"   Output:  {cfg.output_dir}\n"
        f"   Summary: {summary_path}\n"
    )
    return results
