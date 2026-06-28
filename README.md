# doc-engine

A document ingestion and extraction pipeline that classifies mixed-format corpora and converts each file to structured Markdown. It handles Arabic/English PDFs (text-native and scanned), Office documents, and images — automatically routing each file to the most appropriate parser.

The project ships three implementations at different operating points:

| Implementation | Location | When to use |
|---|---|---|
| **Python CLI** | `engine-py/` | Development, single-machine batch jobs |
| **Rust Orchestrator** | `py-rs-version/` | Larger corpora, lower memory, no recompile for parser changes |
| **Deployable API** | `deployable version/` | Production — REST API + async workers + Docker Compose |

All three share the same classification logic and parser scripts.

---

## How it works

```
Raw Documents (input/)
        │
        ▼
 ┌─────────────┐
 │   Detector  │  Classifies each file — zero rendering, O(1) page count via XRef
 └──────┬──────┘
        │
        ▼
 ┌─────────────┐
 │   Sorter    │  Moves each file to a typed subfolder in sorted/
 └──────┬──────┘
        │
        ▼
 ┌──────────────────────────────────────────────────────────┐
 │                    Router / Pipeline                     │
 │                                                          │
 │  OFFICE (DOCX · XLSX · PPTX · ODT)   ──────────────►  Kreuzberg (CPU) │
 │                                                          │
 │  PDF ≤ 10 pages, text-native          ──────────────►  VLM             │
 │  PDF 11–200 pages, text-native        ──────────────►  Docling (GPU)   │
 │  PDF > 200 pages, text-native         ──────────────►  VLM             │
 │                               (head 10 + tail 10 pages extracted first) │
 │                                                          │
 │  PDF ≤ 20 pages, scanned              ──────────────►  VLM             │
 │  PDF > 20 pages, scanned              ──────────────►  VLM             │
 │                               (head 10 + tail 10 pages extracted first) │
 │                                                          │
 │  Images (PNG · JPG · TIFF…)           ──────────────►  VLM             │
 └──────────────────────────────────────────────────────────┘
        │
        ▼
   output/  (one .md per document + _summary.json)
```

**Concurrency:** parsers run as isolated subprocesses (no shared GIL) gated by semaphores — 8 simultaneous Office jobs, 1 Docling (GPU VRAM constraint), 4 VLM.

---

## Classification

Each file is classified before any parsing begins:

1. **File type** — extension check → OFFICE | IMAGE | PDF | UNKNOWN
2. **PDF page count** — read via XRef metadata (O(1), no page rendering).  
   Fallback chain: pypdfium2 → PyMuPDF → brute-force iteration.
3. **Scanned detection** — sample 5 evenly-spaced pages, measure average characters/page.  
   Below 50 chars/page → scanned.
4. **Long PDF preparation** — PDFs > 200 pages (text) or > 20 pages (scanned) are truncated to the first 10 + last 10 pages before parsing, preserving executive summaries and conclusions without processing hundreds of pages.

---

## Parsers

### Kreuzberg — Office documents
Handles DOCX, XLSX, PPTX, ODT, ODS, ODP. Extracts headings, paragraphs, lists, and tables as Markdown pipe-tables. Falls back to Tesseract OCR (Arabic + English, LSTM mode, PSM=3) for embedded images. Garbage-character detection: if >2% of characters are outside Latin/Arabic ranges the extracted text layer is discarded and forced OCR is applied. Runs CPU-only — milliseconds per file.

### Docling — Text-native PDFs (11–200 pages)
GPU-accelerated layout analysis and table detection (TableFormer ACCURATE mode). Exports full structured Markdown with pipe-tables and section headers. Detects Arabic Presentation Forms (visual-order encoding) and forces OCR correction automatically. Applies NFKC normalisation to all Arabic output. `CUDA_VISIBLE_DEVICES=""` is set for the Kreuzberg subprocess to prevent the bundled ONNX Runtime from aborting on Blackwell (sm_120) at C++ boundary.

### VLM — Scanned PDFs, short PDFs, images
Each page is rendered to a 200 DPI base64 PNG and sent to Qwen3.6-27B-FP8 via a vLLM endpoint (OpenAI-compatible API). Pages are dispatched in parallel (4 concurrent requests). The model returns:
- **Document type** — certificate, invoice, contract, org chart, ID, report, …
- **Visual/authentication elements** — stamps, signatures, logos, watermarks, QR codes, seals with description and page location
- **Full verbatim content** — all text in correct Arabic RTL order, tables as Markdown pipe-tables

Retry logic: 3 attempts with exponential backoff (2 s, 4 s, 8 s).

---

## Implementation 1 — Python CLI (`engine-py/`)

Standalone Python application. Each parser runs as an isolated `subprocess.run()` call; a `ThreadPoolExecutor(max_workers=13)` dispatches them concurrently.

### Prerequisites

```bash
# System
sudo apt install tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng

# Python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

A running vLLM instance at an OpenAI-compatible endpoint is required for VLM parsing. Default: `http://197.46.212.11:8000/v1`, model `Qwen/Qwen3.6-27B-FP8`.

The pipeline creates its workspace automatically on first run:
```
<base-dir>/
├── input/     ← drop documents here
├── sorted/    ← pipeline moves files here by type
├── temp/      ← head+tail PDFs written here
└── output/    ← Markdown files written here
```

Default `base-dir` is `/home/nullkuhl/docs` (change in `config.py`).

### Usage

```bash
# Full pipeline: sort input/ then process all sorted files
python main.py

# Override workspace root
python main.py --base-dir /data/docs

# Process a single file (skips sorting)
python main.py --file /path/to/document.pdf

# Process already-sorted files without re-sorting
python main.py --no-sort

# Tune thresholds and VLM
python main.py \
  --long-threshold 200 \
  --head 10 --tail 10 \
  --scan-threshold 50 \
  --vlm-url http://localhost:8000/v1 \
  --vlm-model Qwen/Qwen3.6-27B-FP8 \
  --vlm-workers 4 \
  --vlm-dpi 200
```

### CLI reference

| Flag | Default | Description |
|---|---|---|
| `--base-dir` | `/home/nullkuhl/docs` | Workspace root |
| `--file` | — | Process a single file; bypasses sorting |
| `--no-sort` | false | Skip sorting; process whatever is in `sorted/` |
| `--long-threshold` | 200 | PDFs with more pages than this → head+tail extraction |
| `--head` | 10 | Pages to sample from the start of a long PDF |
| `--tail` | 10 | Pages to sample from the end of a long PDF |
| `--scan-threshold` | 50 | Avg chars/page below this → classified as scanned |
| `--vlm-url` | config value | OpenAI-compatible VLM endpoint base URL |
| `--vlm-model` | config value | VLM model name |
| `--vlm-workers` | 4 | Parallel page requests to VLM |
| `--vlm-dpi` | 200 | DPI for rendering PDF pages before sending to VLM |

### Structure

```
engine-py/
├── main.py              # CLI entry point (argparse)
├── config.py            # Thresholds, paths, VLM endpoint
├── detector.py          # Classification — DocClass enum, O(1) page count
├── sorter.py            # Moves files from input/ to sorted/ by type
├── pipeline.py          # Orchestrator — ThreadPoolExecutor + semaphores
├── parsers/
│   ├── __init__.py      # ParseResult dataclass
│   ├── office.py        # Kreuzberg parser
│   ├── docling_parser.py
│   └── vlm_parser.py
└── requirements.txt
```

---

## Implementation 2 — Rust Orchestrator (`py-rs-version/`)

Rust handles sorting, classification, semaphore routing, and concurrency (tokio async + rayon). Parser logic stays in Python scripts invoked as subprocesses via `Command::output()`. The Python parsers in `py-rs-version/parsers/` are subprocess-wrapper shims around the same parser logic.

lopdf replaces pypdfium2 for PDF page count and head+tail extraction — GIL-free, no Python overhead.

### Build and run

```bash
cargo build --release
./target/release/doc-engine --base-dir /data/docs
./target/release/doc-engine --file /path/to/document.pdf
./target/release/doc-engine --no-sort
```

All CLI flags from the Python version are supported. Python parser scripts must be in the `parsers/` directory adjacent to the binary, and the same venv/system packages apply.

### Structure

```
py-rs-version/
├── Cargo.toml
├── src/
│   ├── main.rs          # CLI entry point (clap)
│   ├── config.rs
│   ├── detector.rs      # Classification via lopdf (PDF XRef, scanned detection)
│   ├── extractor.rs     # Head+tail page extraction
│   ├── pipeline.rs      # Tokio async orchestrator + Arc<Semaphore> gates
│   ├── sorter.rs
│   └── summary.rs
└── parsers/             # Python subprocess wrappers (reused by engine-py too)
    ├── common.py
    ├── office_parser.py
    ├── docling_parser.py
    └── vlm_parser.py
```

---

## Implementation 3 — Deployable API (`deployable version/`)

Production architecture: FastAPI receives uploads, Celery workers process documents asynchronously, Redis stores job state. Runs entirely in Docker Compose.

```
Client
  │
  ▼ POST /api/v1/upload
┌─────┐        ┌────────┐       ┌────────────┐
│ API │──job──►│ Redis  │◄──────│   Worker   │
│     │        │(state) │       │  (Celery)  │
└─────┘        └────────┘       └─────┬──────┘
  │                                   │ pipeline.run()
  ▼ GET /api/v1/result/{job_id}        │
  ◄────────────────────────────────────┘
```

**Job lifecycle:**
1. Client POSTs a document → API saves to `workspace/{job_id}/input/`, queues `process_document(job_id)` in Celery
2. Worker runs the full pipeline, saves Markdown + summary to `workspace/{job_id}/output/`
3. Client polls `GET /status/{job_id}` until `done`
4. Client fetches `GET /result/{job_id}` → combined Markdown + `_summary.json`
5. Redis entries auto-expire after 24 hours

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/upload` | Upload a document; returns `job_id` |
| `GET` | `/api/v1/status/{job_id}` | Returns `queued` / `processing` / `done` / `failed` |
| `GET` | `/api/v1/result/{job_id}` | Returns Markdown content + summary (only when `done`) |
| `GET` | `/api/v1/health` | Pings Redis; returns `ok` or `degraded` |

### Running

```bash
cp .env.example .env   # set VLM_BASE_URL, VLM_MODEL, etc.
docker-compose up -d
```

Services: `redis` (job state), `api` (FastAPI on `:8080`), `worker` (Celery, GPU-enabled).

### Structure

```
deployable version/
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.worker
├── settings.py          # Pydantic environment config
├── schemas.py           # Request/response models
├── logging_config.py
├── api/
│   ├── main.py          # FastAPI app + lifespan
│   └── routes.py        # Upload, status, result, health endpoints
├── worker/
│   ├── celery_app.py
│   └── tasks.py         # process_document Celery task
├── storage/
│   └── manager.py       # Redis job state + disk I/O
└── core/                # Shared pipeline code (mirrors engine-py)
    ├── config.py
    ├── detector.py
    ├── sorter.py
    ├── pipeline.py
    └── parsers/
        ├── office.py
        ├── docling_parser.py
        └── vlm_parser.py
```

---

## Output format

Every document produces a `.md` file with YAML front-matter:

```markdown
---
source: التقرير_السنوي_الشامل_2024.pdf
parser: docling
pages: 40
languages: [Arabic, English]
---

## ملخص تنفيذي

...

## Financial Highlights

| Metric          | 2023  | 2024  | Change |
|-----------------|-------|-------|--------|
| Revenue (SAR M) | 1,240 | 1,415 | +14.1% |
| Net Profit      | 187   | 223   | +19.3% |
```

A `_summary.json` is written after each run:

```json
{
  "total_elapsed_s": 185.84,
  "files": [
    { "source": "report.pdf", "parser": "docling", "pages": 40,
      "ok": true, "elapsed_s": 17.81, "table_count": 12 },
    { "source": "scan.pdf", "parser": "vlm", "pages": 8,
      "ok": true, "elapsed_s": 28.14, "table_count": 0 }
  ]
}
```

---

## Performance

Benchmarked on 35 mixed Arabic/English documents (7 Office, 10 Docling, 18 VLM) on an RTX PRO 6000 (97 GB VRAM) — same machine and vLLM server across all runs.

| Version | Wall-clock | Speedup |
|---|---|---|
| Python Sequential (original) | 660.57 s (11 m 01 s) | 1× |
| **Python Parallel Subprocess** | **185.84 s (3 m 06 s)** | **3.55×** |
| **Rust Orchestrator** | **187.33 s (3 m 07 s)** | **3.52×** |

All 35 files succeeded in every run.

**Why both parallel versions are identical:** The bottleneck is `DOCLING_SLOTS=1` — a single Docling GPU slot forces Docling jobs to run serially regardless of orchestrator. The Docling serial sum *is* the wall-clock time. Office (< 0.15 s total, 8 concurrent) and VLM (519–544 s sum, 4 concurrent) both complete entirely inside the Docling window at zero extra cost. The 1.49 s difference between Python and Rust is GPU scheduling noise on a single file.

Concurrency diagram (both parallel versions):
```
t=0                                                                    t=186s
│
├─ office ── office ── ... (all 7 done < 0.15 s) ────────────────────────┤
│
├─ docling ── VA1 (75s) ── AnnualReport (18s) ── Meridian (19s) ── ... ─┤  SLOT=1
│
├─ vlm ── Cloud (69s) ───────────────────────────────┐                   │
├─ vlm ── Rakans (42s) ─────────────────────────────┤                   │  SLOTS=4
├─ vlm ── arabic_report (43s) ──────────────────────┤                   │
└─ vlm ── (14 more files cycle through 4 slots) ────────────────────────┘
```

**VA1 (135-page PDF) dropped from 181 s to 75 s** when switching to subprocess isolation — running Docling as an in-process import accumulated model state and GPU context overhead across sequential calls; fresh subprocesses start clean every time.

See `benchmark-comparison.md` for the full per-file breakdown.

---

## Configuration reference

All thresholds are tunable via CLI flags or `config.py`:

| Parameter | Default | Meaning |
|---|---|---|
| `vlm_text_threshold` | 10 pages | PDFs ≤ this → VLM (best quality for short docs) |
| `long_pdf_threshold` | 200 pages | PDFs > this → head+tail sampling |
| `scanned_long_threshold` | 20 pages | Scanned PDFs > this → head+tail only |
| `scan_char_threshold` | 50 chars/page | Avg below this → classified as scanned |
| `long_head_pages` | 10 | Pages to take from start of long PDF |
| `long_tail_pages` | 10 | Pages to take from end of long PDF |
| `vlm_max_workers` | 4 | Parallel page requests to vLLM |
| `vlm_image_dpi` | 200 | DPI for PDF → PNG rendering |
| `OFFICE_SLOTS` | 8 | Max concurrent Kreuzberg subprocesses |
| `DOCLING_SLOTS` | 1 | Max concurrent Docling subprocesses (GPU VRAM limit) |
| `VLM_SLOTS` | 4 | Max concurrent VLM subprocesses |
