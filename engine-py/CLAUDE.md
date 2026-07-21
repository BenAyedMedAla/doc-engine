# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo context

This directory (`engine-py/`) is one of three sibling implementations in the `doc-engine` monorepo (see `../README.md` for the full picture):

| Implementation | Location | Purpose |
|---|---|---|
| **Python CLI** | `engine-py/` (this dir) | Development, single-machine batch jobs |
| **Rust Orchestrator** | `../py-rs-version/` | Larger corpora, lower memory, no recompile for parser changes |
| **Deployable API** | `../deployable version/` | Production — FastAPI + Celery + Redis + Docker Compose |

All three share the same classification/routing logic conceptually, but **the actual parser scripts executed at runtime by this Python CLI live in `../py-rs-version/parsers/`, not in `engine-py/parsers/`.**

## Critical gotcha: two `parsers/` directories

`pipeline.py` dispatches each file by running a parser script as a subprocess:

```python
_PARSERS_DIR = Path(__file__).parent.parent / "py-rs-version" / "parsers"
```

It only ever imports one thing from the local `engine-py/parsers/` package — the `ParseResult` dataclass in `parsers/__init__.py`. The parsing logic in `engine-py/parsers/office.py`, `docling_parser.py`, and `vlm_parser.py` is **not on the execution path** — those are effectively a stale/duplicate copy. The scripts that actually run are `../py-rs-version/parsers/office_parser.py`, `docling_parser.py`, and `vlm_parser.py` (invoked via `sys.executable <script> --input ... --output-dir ...`, one Python interpreter per file, no shared GIL).

**If you're asked to change parsing behavior (OCR logic, Markdown rendering, prompts, etc.), edit the scripts in `../py-rs-version/parsers/`, not `engine-py/parsers/`.** Verify which copy is live with `grep -rn "_PARSERS_DIR\|_SCRIPT" pipeline.py` before assuming otherwise — this indirection is easy to miss since the two files are near-identical.

The `../py-rs-version/parsers/*.py` scripts are also invoked by the Rust orchestrator, so changes there affect both implementations.

## Commands

```bash
# Install (system + Python deps)
sudo apt install tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline (sorts workspace/input/ then processes everything)
python main.py

# Process a single file directly (bypasses sorting; still shells out via pipeline._process_file)
python main.py --file /path/to/document.pdf

# Re-process already-sorted files without re-sorting
python main.py --no-sort

# Override workspace root / VLM endpoint / thresholds
python main.py --base-dir /data/docs --vlm-url http://localhost:8000/v1 --vlm-model Qwen/Qwen3.6-27B-FP8
python main.py --long-threshold 200 --head 10 --tail 10 --scan-threshold 50

# Run the batch REST API (single process, no Celery/Redis — see api.py docstring)
uvicorn api:app --host 0.0.0.0 --port 8080 --workers 1   # must stay at 1 worker: batch state is in-memory

# Recursively process a nested evidence tree (content-deduplicated, bypasses sorter)
python run_evidence.py
```

There is no test suite, linter, or type-checker configured in this directory — nothing to run for CI-style checks.

Default workspace root is `/home/nullkuhl/docs` (`config.py: Config.base_dir`), separate from the `workspace/` directory present in this repo (used by `api.py` per-batch, `DOC_ENGINE_WORKSPACE` env var).

## Architecture

Pipeline stages, in order:

1. **Sort** (`sorter.py`) — moves each file from `<base_dir>/input/` into a typed subfolder under `<base_dir>/sorted/` (`office/`, `images/`, `pdfs/{vlm_text,short_text,short_scanned,long_text,long_scanned}/`). Classification runs sequentially because pypdfium2's C library is not thread-safe.
2. **Classify** (`detector.py`) — `classify(path, cfg) -> DocClass`, extension-based for Office/images; for PDFs, page count comes from a 3-tier fallback (pypdfium2 XRef → PyMuPDF repair → brute-force page iteration), and "scanned" is detected by sampling `scan_sample_pages` (default 5) evenly-spaced pages and checking average chars/page against `scan_char_threshold` (default 50) — no page rendering happens at this stage.
3. **Prepare long PDFs** (`detector.extract_pdf_pages`) — PDFs over `long_pdf_threshold` (text) or `scanned_long_threshold` (scanned) pages get a temp file built from just the first `long_head_pages` + last `long_tail_pages` before parsing, so exec summaries/conclusions are covered without processing hundreds of pages.
4. **Dispatch** (`pipeline.run` / `pipeline._process_file`) — one subprocess per file, gated by module-level semaphores that must not be changed casually since they encode real hardware constraints:
   - `_OFFICE_SLOTS = 8` — CPU-only, sub-second, safe to run many concurrently
   - `_DOCLING_SLOTS = 1` — GPU-bound; 2+ concurrent Docling processes cause VRAM OOM
   - `_VLM_SLOTS = 4` — I/O-bound network calls to the vLLM server
   
   A `ThreadPoolExecutor(max_workers=13)` (sum of the slots above) submits all files; each thread blocks on the relevant semaphore, then `subprocess.run()`s the parser script and parses one trailing JSON line from its stdout for status/page count/table count. Parser stdout is otherwise ignored — the parser subprocess writes the `.md` file directly to `output_dir`.
5. **Summary** — `<base_dir>/output/_summary.json`, written once after all subprocesses complete: per-file parser/pages/ok/error/elapsed_s/table_count plus total elapsed time.

### Routing table (`DocClass` → parser)

| Class | Condition | Parser |
|---|---|---|
| `OFFICE` | `.docx/.xlsx/.pptx/...` | Kreuzberg (CPU, Tesseract ara+eng OCR fallback) |
| `PDF_VLM_TEXT` | text-native, ≤ 4 pages | VLM |
| `PDF_SHORT_TEXT` | text-native, 5–200 pages | Docling (GPU, TableFormer ACCURATE) |
| `PDF_LONG_TEXT` | text-native, > 200 pages | VLM, head+tail only |
| `PDF_SHORT_SCAN` | scanned, ≤ 20 pages | VLM |
| `PDF_LONG_SCAN` | scanned, > 20 pages | VLM, head+tail only |
| `IMAGE` | `.png/.jpg/...` | VLM |
| `UNKNOWN` | unreadable/encrypted PDF or unrecognised extension | skipped |

In `pipeline.py`, only `OFFICE` and `PDF_SHORT_TEXT` map to a named script (`office_parser.py`, `docling_parser.py`); every other class falls through to `vlm_parser.py`.

### Arabic-specific handling (spread across parser scripts, not this directory)

- Docling: detects Arabic Presentation Forms (old visual-order Unicode, U+FB50–FEFF) — if >30% of Arabic characters are in that range, it re-runs with forced OCR to get correct logical order, then applies NFKC normalization.
- Kreuzberg (Office): Tesseract `ara+eng`, LSTM-only (`oem=1`), PSM 3; if >2% of extracted characters fall outside Arabic/Latin ranges, forces a second OCR pass.
- VLM: system prompt explicitly instructs RTL-correct verbatim reproduction of Arabic text; a bidi-control-character stripper (`_BIDI` regex) runs on all parser output.

### `api.py` batch model

Single FastAPI process, no external queue — each batch runs in Starlette's background threadpool calling `pipeline.run()` directly. Batch state (`_batches: dict`) is in-memory and per-process, which is why `--workers` must stay at 1; the per-parser semaphores in `pipeline.py` are module-level globals, so concurrent batches within that one process still share the same GPU/CPU concurrency limits. Each batch gets its own `Config(base_dir=workspace/<batch_id>)`.

### `run_evidence.py`

A one-off recursive variant: walks a fixed nested directory (`EVIDENCE_ROOT`), MD5-hashes every file to dedupe identical evidence reused across multiple controls, and calls `pipeline.run(cfg, sort_first=False, input_paths=files)` directly — bypassing `sorter.py` (which only scans `input/` non-recursively). Originals are never moved; output lands flat in `<base_dir>/output/`.
