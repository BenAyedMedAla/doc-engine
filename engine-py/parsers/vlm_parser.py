#!/usr/bin/env python3
"""
VLM parser — scanned PDFs and images → structured Markdown.
Invoked as a subprocess by pipeline.py.

Pages are rendered at IMAGE_DPI and sent to an OpenAI-compatible vision
endpoint (vLLM).  Requests are dispatched in parallel via a thread pool.

Usage:
  python3 vlm_parser.py --input <file> --output-dir <dir> [VLM options]

Prints one JSON line to stdout on completion (read by the orchestrator).
"""
from __future__ import annotations

import argparse
import base64
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from common import ParseResult

# ── Helpers ───────────────────────────────────────────────────────────────────

_BIDI = re.compile(r"[\u200E\u200F\u202A-\u202E\u2066-\u2069؜﻿]")


def _strip_bidi(text: str) -> str:
    return _BIDI.sub("", text)


def _count_md_tables(text: str) -> int:
    in_table = count = 0
    for line in text.splitlines():
        is_row = line.strip().startswith("|") and line.strip().endswith("|")
        if is_row and not in_table:
            in_table = True
            count += 1
        elif not is_row:
            in_table = False
    return count


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert multilingual document analyst specialising in Arabic and English documents.
Your role: extract every piece of information from document page images with complete accuracy
and structure the result as clean, well-formed Markdown.

OUTPUT FORMAT — follow this order exactly:

---
> **Document type:** <precise type>

Examples: Certificate of Graduation, Invoice / فاتورة, Contract / عقد, \
Organisational Chart, Identity Document, Bank Statement, Medical Report, \
Payslip, Legal Notice, Policy Document, Meeting Minutes, Technical Report, \
Vulnerability Assessment, etc. Infer confidently from layout and content.

---
For EACH non-text visual element detected on this page add one block:

> **Element:** <element type>
> **Description:** <what it shows, says, or represents>
> **By / Issuer:** <name or organisation — if readable> *(omit if unknown)*
> **Location:** <position on page — e.g. top-right, over text, footer, background>

Detect ALL of the following (and anything else you observe):
  Handwritten or printed signatures · Official rubber stamps / أختام
  Company / institutional logos · Watermarks (text or image-based)
  Photographs / portraits · Decorative certificate borders or frames
  QR codes or barcodes (include decoded value if readable)
  Fingerprints or biometric marks · Embossed or raised impressions
  Digital signature blocks (DocuSign, Adobe Sign, …)
  Notarial / apostille stickers · Security holograms or foil elements
  Illustrations, diagrams, charts, org-chart boxes

If NO such elements exist on this page — skip this section entirely.

---
## Full Content

Reproduce ALL text from the page below, rules:
- Never summarise or paraphrase — extract verbatim.
- Arabic text: preserve exactly, right-to-left reading order.
- Tables: render as Markdown pipe-tables (| col | col |).
- Use ## for main headings, ### for sub-headings.
- Include page numbers, footnotes, headers, footers — nothing omitted.
- Do NOT wrap output in ```markdown``` fences.\
"""

CONTENT_ONLY_PROMPT = """\
Extract the full content of this page as structured Markdown.

Rules:
- Reproduce ALL text verbatim — no summarisation.
- Arabic text: preserve exactly in RTL reading order.
- Tables: render as Markdown pipe-tables.
- Use ## for section headings, ### for sub-headings.
- List any stamps, signatures, logos, or visual elements as:
    > **Element:** <type> | **Location:** <position>
- Include page numbers, footnotes, headers, footers.
- Do NOT wrap in ```markdown``` fences.\
"""


# ── Image encoding ────────────────────────────────────────────────────────────

def _pil_to_b64(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.standard_b64encode(buf.getvalue()).decode()


def _pdf_page_to_pil(path: Path, page_idx: int, dpi: int):
    import pypdfium2 as pdfium
    doc    = pdfium.PdfDocument(str(path))
    page   = doc[page_idx]
    bitmap = page.render(scale=dpi / 72.0)
    pil    = bitmap.to_pil()
    doc.close()
    return pil


def _image_to_pil(path: Path):
    from PIL import Image
    return Image.open(str(path)).convert("RGB")


# ── CPU OCR fallback (used when the VLM request fails after all retries) ──────
# Keeps a page from silently coming back empty when the GPU/vLLM server has a
# problem — degrades to local Tesseract OCR instead of losing the page.

def _cpu_ocr_fallback(pil_img) -> str:
    import subprocess
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            pil_img.save(tmp.name, format="PNG")
            proc = subprocess.run(
                ["tesseract", tmp.name, "stdout", "-l", "ara+eng", "--psm", "3"],
                capture_output=True, text=True, timeout=120,
            )
        text = (proc.stdout or "").strip()
        return text if text else "*(CPU OCR fallback produced no text)*"
    except Exception as exc:
        return f"*(CPU OCR fallback also failed: {exc})*"


def _call_page_with_fallback(client, args, pil_img, is_first: bool) -> tuple[str, bool]:
    """Returns (content, used_cpu_fallback)."""
    b64_url = _pil_to_b64(pil_img)
    try:
        return _call_page(client, args, b64_url, is_first), False
    except Exception as exc:
        print(f"    [vlm] page error, falling back to CPU OCR: {exc}", file=sys.stderr)
        ocr_text = _cpu_ocr_fallback(pil_img)
        note = (
            "> ⚠ VLM request failed — recovered via CPU OCR fallback (Tesseract).\n"
            "> Visual-element detection and table structure are unavailable for this page.\n\n"
        )
        return note + ocr_text, True


# ── VLM API call ──────────────────────────────────────────────────────────────

def _call_vision(client, model, b64_url, prompt, max_tokens, retries, backoff) -> str:
    last_exc = None
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": b64_url}},
                        {"type": "text",      "text": prompt},
                    ]},
                ],
                max_tokens=max_tokens,
                temperature=0,
                timeout=180,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(backoff ** attempt)
    raise last_exc


def _call_page(client, args, b64_url: str, is_first: bool) -> str:
    prompt = (
        "Analyse this document page fully. Follow the output format in the system prompt exactly."
        if is_first else CONTENT_ONLY_PROMPT
    )
    return _call_vision(
        client, args.vlm_model, b64_url, prompt,
        args.vlm_tokens, args.vlm_retries, args.vlm_backoff,
    )


# ── PDF / image extraction ────────────────────────────────────────────────────

def _extract_pdf(client, args, path: Path) -> tuple[str, int, int, bool]:
    import pypdfium2 as pdfium
    doc        = pdfium.PdfDocument(str(path))
    page_count = len(doc)
    doc.close()

    pil_pages = [_pdf_page_to_pil(path, i, args.vlm_dpi) for i in range(page_count)]

    results: list[str] = [""] * page_count
    fallback_used = [False] * page_count
    with ThreadPoolExecutor(max_workers=args.vlm_workers) as pool:
        futures = {
            pool.submit(_call_page_with_fallback, client, args, img, i == 0): i
            for i, img in enumerate(pil_pages)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx], fallback_used[idx] = future.result()
            except Exception as exc:
                print(f"    [vlm] page {idx + 1} failed completely: {exc}", file=sys.stderr)
                results[idx] = f"\n\n> ⚠ Page {idx + 1} extraction failed (VLM and CPU fallback both failed): {exc}\n\n"
                fallback_used[idx] = True

    parts: list[str] = []
    for i, text in enumerate(results):
        if not text.strip():
            continue
        if i > 0:
            parts.append(f"\n\n---\n*Page {i + 1}*\n\n")
        parts.append(text)

    combined = _strip_bidi("".join(parts))
    return combined, _count_md_tables(combined), page_count, any(fallback_used)


def _extract_image(client, args, path: Path) -> tuple[str, int, int, bool]:
    pil_img = _image_to_pil(path)
    text, used_fallback = _call_page_with_fallback(client, args, pil_img, is_first=True)
    text = _strip_bidi(text)
    return text, _count_md_tables(text), 1, used_fallback


# ── Parser ────────────────────────────────────────────────────────────────────

def parse(path: Path, args) -> ParseResult:
    try:
        import openai
        client = openai.OpenAI(base_url=args.vlm_url, api_key="none")

        suf = path.suffix.lower()
        if suf == ".pdf":
            content, table_count, page_count, used_fallback = _extract_pdf(client, args, path)
        else:
            content, table_count, page_count, used_fallback = _extract_image(client, args, path)

        header = (
            f"---\n"
            f"source: {path.name}\n"
            f"parser: vlm\n"
            f"model: {args.vlm_model}\n"
            f"pages: {page_count}\n"
            f"cpu_fallback: {used_fallback}\n"
            f"---\n\n"
        )

        return ParseResult(
            source=path, parser="vlm",
            content=header + content, page_count=page_count,
            extras={"table_count": table_count, "cpu_fallback": used_fallback},
        )

    except Exception as exc:
        return ParseResult(source=path, parser="vlm", content="", error=str(exc))


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input",      type=Path,  required=True)
    p.add_argument("--output-dir", type=Path,  required=True)
    p.add_argument("--vlm-url",     default="http://127.0.0.1:8000/v1")
    p.add_argument("--vlm-model",   default="Qwen/Qwen3.5-9B")
    p.add_argument("--vlm-tokens",  type=int,   default=8192)
    p.add_argument("--vlm-dpi",     type=int,   default=200)
    p.add_argument("--vlm-workers", type=int,   default=4)
    p.add_argument("--vlm-retries", type=int,   default=3)
    p.add_argument("--vlm-backoff", type=float, default=2.0)
    args = p.parse_args()

    result = parse(args.input, args)
    if result.ok:
        result.save(args.output_dir)
    result.emit()


if __name__ == "__main__":
    main()
