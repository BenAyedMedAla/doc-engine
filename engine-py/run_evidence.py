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
import time
from pathlib import Path

from config import Config
from pipeline import run

EVIDENCE_ROOT = Path("/home/nullkuhl/docs/input/EVIDENCE")
REPORT_PATH = Path("/home/nullkuhl/docs/evidence_report.txt")


def _fmt(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h}h {m}m {s:.1f}s" if h else (f"{m}m {s:.1f}s" if m else f"{s:.1f}s")


def _hash(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    t_start = time.time()

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

    t_hashed = time.time()
    print(f"Found {len(all_files)} files under {EVIDENCE_ROOT}, "
          f"{len(files)} unique by content — processing unique set only")

    results = run(cfg, sort_first=False, input_paths=files)

    t_end = time.time()

    ok = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    missing = len(files) - len(results)  # files that never got dispatched at all

    lines = []
    lines.append("── Evidence run report ──────────────────────────────────")
    lines.append(f"Total files found (incl. duplicates): {len(all_files)}")
    lines.append(f"Unique files (by content) submitted:  {len(files)}")
    lines.append(f"Results returned:                     {len(results)}")
    lines.append(f"  Succeeded: {len(ok)}")
    lines.append(f"  Failed:    {len(failed)}")
    if missing:
        lines.append(f"  MISSING (never dispatched):  {missing}")
    lines.append(
        "All unique files processed successfully."
        if not failed and not missing
        else "NOT all unique files were processed successfully — see failures below."
    )
    if failed:
        lines.append("\nFailed files:")
        for r in failed:
            lines.append(f"  - {r.source}: {r.error}")
    lines.append("")
    lines.append(f"Hashing/dedup time: {_fmt(t_hashed - t_start)}")
    lines.append(f"Processing time:    {_fmt(t_end - t_hashed)}")
    lines.append(f"Total time:         {_fmt(t_end - t_start)}")

    report = "\n".join(lines)
    print("\n" + report)
    REPORT_PATH.write_text(report + "\n", encoding="utf-8")
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
