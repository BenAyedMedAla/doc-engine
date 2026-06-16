#!/usr/bin/env python3
"""
Document ingestion & extraction pipeline — CLI entry point.

Usage examples:

  # Sort everything in docs/input/ then process all of it
  python main.py

  # Process a single specific file (bypasses sorting)
  python main.py --file /path/to/document.pdf

  # Process all already-sorted files without re-sorting
  python main.py --no-sort

  # Override workspace and VLM endpoint
  python main.py --base-dir /data/docs --vlm-url http://localhost:8000/v1

  # Change PDF length threshold or page sampling
  python main.py --long-threshold 30 --head 5 --tail 5

The pipeline Python environment (benchmark-1/myenv) must be active, or invoke
directly:
  /home/nullkuhl/docling-kreuzberg-benchmark-1/myenv/bin/python3 main.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from any cwd
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from pipeline import run


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Document ingestion pipeline: sorts and extracts to Markdown.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Workspace
    p.add_argument("--base-dir", type=Path, default=None,
                   help="Workspace root (contains input/, sorted/, output/).")

    # Run modes
    p.add_argument("--no-sort", action="store_true",
                   help="Skip sorting; process whatever is already in sorted/.")
    p.add_argument("--file", type=Path, default=None,
                   help="Process a single file directly (skips sorting).")

    # PDF thresholds
    p.add_argument("--long-threshold", type=int, default=None,
                   help="Pages above this count → long PDF (default: 50).")
    p.add_argument("--head", type=int, default=None,
                   help="Pages to take from the start of a long PDF (default: 10).")
    p.add_argument("--tail", type=int, default=None,
                   help="Pages to take from the end of a long PDF (default: 10).")
    p.add_argument("--scan-threshold", type=int, default=None,
                   help="Avg chars/page below this → scanned PDF (default: 50).")

    # VLM
    p.add_argument("--vlm-url", type=str, default=None,
                   help="OpenAI-compatible VLM endpoint base URL.")
    p.add_argument("--vlm-model", type=str, default=None,
                   help="VLM model name to request.")
    p.add_argument("--vlm-workers", type=int, default=None,
                   help="Parallel page requests to VLM (default: 4).")
    p.add_argument("--vlm-dpi", type=int, default=None,
                   help="DPI for rendering PDF pages before sending to VLM (default: 200).")

    return p.parse_args()


def main() -> None:
    args = _parse_args()
    cfg  = Config()

    # Apply overrides
    if args.base_dir:
        cfg.base_dir = args.base_dir
    if args.long_threshold is not None:
        cfg.long_pdf_threshold = args.long_threshold
    if args.head is not None:
        cfg.long_head_pages = args.head
    if args.tail is not None:
        cfg.long_tail_pages = args.tail
    if args.scan_threshold is not None:
        cfg.scan_char_threshold = args.scan_threshold
    if args.vlm_url:
        cfg.vlm_base_url = args.vlm_url
    if args.vlm_model:
        cfg.vlm_model = args.vlm_model
    if args.vlm_workers is not None:
        cfg.vlm_max_workers = args.vlm_workers
    if args.vlm_dpi is not None:
        cfg.vlm_image_dpi = args.vlm_dpi

    print("── Document Ingestion Pipeline ─────────────────────────────────")
    print(f"   Workspace : {cfg.base_dir}")
    print(f"   VLM       : {cfg.vlm_base_url}  ({cfg.vlm_model})")
    print(f"   Long PDF  : > {cfg.long_pdf_threshold} pages  "
          f"→ head {cfg.long_head_pages} + tail {cfg.long_tail_pages}")

    if args.file:
        # Single-file mode — classify and process directly
        from detector import classify
        from pipeline import _process_file
        cfg.ensure_dirs()
        path = args.file.resolve()
        cls  = classify(path, cfg)
        print(f"\n  Single file: {path.name}  [{cls.name}]")
        result = _process_file(path, cls, cfg, cfg.output_dir)
        if result.ok:
            print(f"  Saved → {cfg.output_dir / (path.stem + '.md')}")
        else:
            print(f"  ERROR: {result.error}", file=sys.stderr)
            sys.exit(1)
    else:
        run(cfg, sort_first=not args.no_sort)


if __name__ == "__main__":
    main()
