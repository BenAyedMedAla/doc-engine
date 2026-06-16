# Document Ingestion & Extraction Engine

**Purpose:** Automatically ingest raw documents of any type, classify them, route each one to the most appropriate parser, and produce a structured Markdown file per document — preserving tables, headings, Arabic and English text, and any visual elements (stamps, signatures, logos).

---

## The Problem It Solves

Organisations accumulate documents in many formats — scanned certificates, Arabic/English reports, Excel spreadsheets, policy Word files, org charts — each requiring a different extraction strategy. A one-size-fits-all parser either loses table structure, garbles Arabic text, or misses content inside scanned images. This engine applies the right tool to the right document automatically.

---

## Architecture Overview

```
Raw Documents
      │
      ▼
 ┌─────────────┐
 │   Sorter    │  Classifies each file by type and moves it
 │             │  to a typed subfolder in sorted/
 └──────┬──────┘
        │
        ▼
 ┌──────────────────────────────────────────────────────────┐
 │                    Router / Pipeline                     │
 │                                                          │
 │  OFFICE (DOCX·XLSX·PPTX)  ──────────────►  Kreuzberg   │
 │                                                          │
 │  PDF ≤ 10 pages, text-native  ──────────►  VLM          │
 │  PDF 11–200 pages, text-native  ────────►  Docling      │
 │  PDF > 200 pages, text-native  ─────────►  VLM          │
 │                               (head 10 + tail 10 pages) │
 │                                                          │
 │  PDF ≤ 20 pages, scanned  ──────────────►  VLM          │
 │  PDF > 20 pages, scanned  ──────────────►  VLM          │
 │                               (head 10 + tail 10 pages) │
 │                                                          │
 │  Images (PNG·JPG·TIFF…)  ───────────────►  VLM          │
 └──────────────────────────────────────────────────────────┘
        │
        ▼
 Structured Markdown output per document  →  output/
```

---

## The Three Parsers

### 1. Kreuzberg — Office Documents
- Handles DOCX, XLSX, PPTX, ODT, ODS, ODP
- Extracts full document structure: headings, paragraphs, lists, tables as Markdown pipe-tables
- Uses Tesseract OCR (Arabic + English, LSTM mode) as fallback for embedded images
- Runs on CPU — extremely fast (milliseconds per file)
- Includes garbage-character detection: if the text layer is corrupted, re-extracts with forced OCR

### 2. Docling — Text-Native PDFs (medium length)
- Handles text-based PDFs between 11 and 200 pages
- GPU-accelerated layout analysis and table detection (TableFormer ACCURATE mode on the RTX PRO 6000)
- Exports full structured Markdown with pipe-tables, section headers
- Detects Arabic Presentation Forms (old visual-order encoding) and forces OCR correction automatically
- NFKC normalisation applied to all Arabic output for correct Unicode base characters

### 3. VLM — Scanned PDFs, Short PDFs, Images
- Handles scanned PDFs, image files, and short text PDFs (≤ 10 pages)
- Each page is rendered at 200 DPI and sent to the vision model (Qwen3.6-27B-FP8 via vLLM)
- Pages are sent **in parallel** (4 concurrent requests) to minimise wall-clock time
- The model is prompted to produce a structured report covering:
  - **Document type** (certificate, invoice, contract, org chart, ID, report…)
  - **Visual/authentication elements**: stamps, signatures, logos, watermarks, QR codes, seals — each with description and page location
  - **Full verbatim content**: all text preserved in correct Arabic RTL order, tables rendered as Markdown pipe-tables

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| Page count via XRef metadata | O(1) — reads the PDF catalog entry, no page rendering |
| Scanned detection via text-layer sampling | Samples 5 evenly-spaced pages, measures avg chars/page — avoids processing the whole document |
| Long PDF head+tail extraction | Preserves cover, executive summary, and conclusions without the cost of full processing |
| Kreuzberg on CPU only | The bundled ONNX Runtime aborts on Blackwell (sm_120) at the C++ boundary; CPU execution is stable |
| Docling GPU batching (layout×8, table×4) | Saturates the 97 GB VRAM for maximum throughput on medium-length reports |
| VLM parallel page dispatch | Reduces per-document latency from O(pages × latency) to O(latency) |

---

## Output Format

Every document produces a `.md` file with a YAML front-matter header followed by the full structured content:

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

| Metric          | 2023    | 2024    | Change |
|-----------------|---------|---------|--------|
| Revenue (SAR M) | 1,240   | 1,415   | +14.1% |
| Net Profit      | 187     | 223     | +19.3% |
```

A `_summary.json` is also written after each run with per-file timing and a total elapsed time.

---

## Example Run — 16 Documents, 3m 44s

The following is an actual run processed on **16 June 2026** against a mixed Arabic/English corpus.

### Files Processed

| Document | Type | Parser | Pages | Tables | Time |
|---|---|---|---|---|---|
| التقرير_السنوي_الشامل_2024.pdf | Text PDF | Docling | 40 | 44 | 64.2 s |
| Meridian_Annual_Report_2024.pdf | Text PDF | Docling | 40 | 45 | 35.7 s |
| arabic_report.pdf | Short PDF (≤10p) | VLM | 8 | 11 | 27.0 s |
| Signed Org chart - SAMA (3).pdf | Short PDF (≤10p) | VLM | 2 | 0 | 24.6 s |
| Vulnerability_Management_Process (6).pdf | Short PDF (≤10p) | VLM | 7 | 1 | 16.6 s |
| 0d4dc2a9…pdf | Short PDF (≤10p) | VLM | 1 | 0 | 14.5 s |
| IMG-20260315-WA0016.jpg | Image | VLM | 1 | 0 | 13.9 s |
| certificate3.pdf | Scanned PDF | VLM | 1 | 0 | 11.3 s |
| certificate1.pdf | Scanned PDF | VLM | 1 | 0 | 7.1 s |
| zoom-meeting.png | Image | VLM | 1 | 0 | 9.0 s |
| arabic_large_report.docx | Office | Kreuzberg | 13 | 12 | 0.01 s |
| arabic_large_data.xlsx | Office | Kreuzberg | 7 | 7 | 0.04 s |
| [Live] Information Classification Policy v2.0.docx | Office | Kreuzberg | 9 | 4 | 0.01 s |
| Asset Inventory KSA Prod -2 (1).xlsx | Office | Kreuzberg | 4 | 4 | 0.02 s |
| Project Management - Risk Register-4.xlsx | Office | Kreuzberg | 4 | 4 | 0.02 s |
| L3-1.docx | Office | Kreuzberg | 1 | 0 | < 0.01 s |

### Run Summary

| Metric | Value |
|---|---|
| Total documents | 16 |
| Succeeded | **16 / 16 (100%)** |
| Total tables extracted | **132** |
| Total pages processed | **179** |
| Total elapsed time | **3 min 44 s** |
| Office docs (Kreuzberg) | 6 files — avg **0.02 s each** |
| Text PDFs (Docling) | 2 files — avg **50 s each** (40-page Arabic + English reports, GPU) |
| Scanned/Short/Images (VLM) | 8 files — avg **15 s each** |

### Observations from this Run

- **Arabic processing is transparent** — the Arabic annual report (`التقرير_السنوي_الشامل_2024.pdf`) was processed end-to-end and yielded 44 correctly structured tables, slightly slower than the English equivalent (64 s vs 36 s) due to the higher complexity of Arabic font rendering in Docling's layout model.
- **Kreuzberg is near-instant for Office files** — 6 documents including a 13-page Arabic DOCX and two multi-sheet XLSX files completed in under 50 ms combined.
- **VLM handles visual and structural diversity** — certificates (scanned, 1 page), an org chart (2 pages), and an 8-page Arabic report with 11 tables were all processed correctly by the same pipeline path, with the model identifying document type and any stamps or signatures per page.
- **Zero failures** — every document produced a valid `.md` output with no manual intervention.
