# doc-engine

A document ingestion and extraction pipeline that classifies mixed-format document corpora and converts each file to structured Markdown. It handles Arabic/English PDFs (text-native and scanned), Office documents, and images — automatically routing each file to the most appropriate parser.

---

## How it works

```
Raw Documents (input/)
        │
        ▼
 ┌─────────────┐
 │   Sorter    │  Classifies each file and moves it to a typed subfolder in sorted/
 └──────┬──────┘
        │
        ▼
 ┌──────────────────────────────────────────────────────────┐
 │                    Router / Pipeline                     │
 │                                                          │
 │  OFFICE (DOCX · XLSX · PPTX)  ──────────────►  Kreuzberg│
 │                                                          │
 │  PDF ≤ 10 pages, text-native  ──────────────►  VLM      │
 │  PDF 11–200 pages, text-native  ────────────►  Docling   │
 │  PDF > 200 pages, text-native  ─────────────►  VLM      │
 │                               (head 10 + tail 10 pages) │
 │                                                          │
 │  PDF ≤ 20 pages, scanned  ──────────────────►  VLM      │
 │  PDF > 20 pages, scanned  ──────────────────►  VLM      │
 │                               (head 10 + tail 10 pages) │
 │                                                          │
 │  Images (PNG · JPG · TIFF…)  ───────────────►  VLM      │
 └──────────────────────────────────────────────────────────┘
        │
        ▼
   output/  (one .md per document + _summary.json)
```

---

## Parsers

### Kreuzberg — Office documents
Handles DOCX, XLSX, PPTX, ODT, ODS, ODP. Extracts headings, paragraphs, lists, and tables as Markdown pipe-tables. Falls back to Tesseract OCR (Arabic + English, LSTM mode) for embedded images. Includes garbage-character detection: if the extracted text layer is corrupted it re-extracts with forced OCR. Runs on CPU — milliseconds per file.

### Docling — Text-native PDFs (11–200 pages)
GPU-accelerated layout analysis and table detection (TableFormer ACCURATE mode). Exports full structured Markdown with pipe-tables and section headers. Detects Arabic Presentation Forms and forces OCR correction automatically. Applies NFKC normalisation to all Arabic output.

### VLM — Scanned PDFs, short PDFs, images
Each page is rendered at 200 DPI and sent to Qwen3.6-27B-FP8 via a vLLM endpoint. Pages are dispatched in parallel (4 concurrent requests). The model is prompted to return:
- **Document type** (certificate, invoice, contract, org chart, ID, report…)
- **Visual/authentication elements**: stamps, signatures, logos, watermarks, QR codes, seals — with description and page location
- **Full verbatim content**: all text in correct Arabic RTL order, tables as Markdown pipe-tables

---

## Prerequisites

**System packages**
```bash
sudo apt install tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng
```

**Python environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**VLM server** — a running vLLM instance exposing an OpenAI-compatible endpoint. The default config points to `http://197.46.212.11:8000/v1` with model `Qwen/Qwen3.6-27B-FP8`. Override via `--vlm-url` and `--vlm-model`.

**Workspace layout** — the pipeline expects a directory with this structure (created automatically on first run):
```
<base-dir>/
├── input/     ← drop documents here
├── sorted/    ← pipeline moves files here by type
└── output/    ← Markdown files written here
```
Default `base-dir` is `/home/nullkuhl/docs` (set in `config.py`).

---

## Usage

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
| `--base-dir` | `/home/nullkuhl/docs` | Workspace root (contains `input/`, `sorted/`, `output/`) |
| `--file` | — | Process a single file directly; bypasses sorting |
| `--no-sort` | false | Skip sorting; process whatever is already in `sorted/` |
| `--long-threshold` | 50 | PDFs with more pages than this are treated as "long" (head+tail extraction) |
| `--head` | 10 | Pages to sample from the start of a long PDF |
| `--tail` | 10 | Pages to sample from the end of a long PDF |
| `--scan-threshold` | 50 | Avg chars/page below this value → PDF is classified as scanned |
| `--vlm-url` | config value | OpenAI-compatible VLM endpoint base URL |
| `--vlm-model` | config value | VLM model name |
| `--vlm-workers` | 4 | Parallel page requests to VLM |
| `--vlm-dpi` | 200 | DPI for rendering PDF pages before sending to VLM |

---

## Output format

Every document produces a `.md` file with a YAML front-matter header:

```markdown
---
source: التقرير_السنوي_الشامل_2024.pdf
parser: docling
pages: 40
gpu: true
---

## ملخص تنفيذي

...

## Financial Highlights

| Metric          | 2023  | 2024  | Change |
|-----------------|-------|-------|--------|
| Revenue (SAR M) | 1,240 | 1,415 | +14.1% |
| Net Profit      | 187   | 223   | +19.3% |
```

A `_summary.json` is written after each run with per-file timing, parser used, page count, and success/error counts.

---

## Performance

Benchmarked on 16 mixed Arabic/English documents (June 2026) on an RTX PRO 6000 (97 GB VRAM):

| Parser | Files | Avg time |
|---|---|---|
| Kreuzberg (Office) | 6 | ~0.02 s |
| Docling (text PDFs, 40 pages) | 2 | ~50 s |
| VLM (scanned, short, images) | 8 | ~15 s |
| **Total** | **16** | **3 min 44 s** |

16/16 succeeded with zero manual intervention.

---

## Project structure

```
doc-engine/
├── main.py              # CLI entry point
├── config.py            # Thresholds, paths, VLM endpoint
├── detector.py          # Document classification (O(1) page count via XRef)
├── sorter.py            # Moves files from input/ to sorted/ by type
├── pipeline.py          # Main orchestrator
├── parsers/
│   ├── __init__.py      # ParseResult dataclass
│   ├── office.py        # Kreuzberg parser
│   ├── docling_parser.py# Docling parser
│   └── vlm_parser.py    # VLM parser
└── requirements.txt
```
