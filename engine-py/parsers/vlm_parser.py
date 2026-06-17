#!/usr/bin/env python3
"""
VLM parser — scanned PDFs and raw images → structured Markdown.

Sends each page (rendered at IMAGE_DPI) to an OpenAI-compatible vision API
(vLLM serving Qwen3-VL or similar).  Pages are dispatched in parallel via a
thread pool; results are reassembled in order and combined into one document.

The SYSTEM_PROMPT instructs the model to:
  1. Identify the document type (certificate, invoice, contract, …)
  2. Catalogue every non-text visual element (stamps, signatures, logos,
     watermarks, barcodes, QR codes, seals, …) with location and description
  3. Reproduce all text faithfully — preserving Arabic RTL, rendering tables
     as GFM pipe-tables, using ## / ### for section headings

Multi-page strategy:
  - Page 1: full prompt (metadata + content)
  - Pages 2+: content-only prompt (no repeated metadata block)
  - Final output: YAML front-matter + combined page sections
"""
from __future__ import annotations

import base64
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from config import Config
from parsers import ParseResult

# ── Bidi helper ───────────────────────────────────────────────────────────────

_BIDI = re.compile(r"[\u200E\u200F\u202A-\u202E\u2066-\u2069؜﻿]")


def _strip_bidi(text: str) -> str:
    return _BIDI.sub("", text)


def _count_md_tables(text: str) -> int:
    in_table, count = False, 0
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


# ── Image helpers ─────────────────────────────────────────────────────────────

def _pil_to_b64_url(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.standard_b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _bytes_to_b64_url(data: bytes) -> str:
    b64 = base64.standard_b64encode(data).decode()
    return f"data:image/png;base64,{b64}"


def _pdf_page_to_b64_url(path: Path, page_idx: int, dpi: int) -> str:
    import pypdfium2 as pdfium
    doc    = pdfium.PdfDocument(str(path))
    page   = doc[page_idx]
    scale  = dpi / 72.0
    bitmap = page.render(scale=scale)
    pil_img = bitmap.to_pil()
    doc.close()
    return _pil_to_b64_url(pil_img)


def _image_to_b64_url(path: Path) -> str:
    from PIL import Image
    img = Image.open(str(path))
    return _pil_to_b64_url(img)


# ── VLM API call ──────────────────────────────────────────────────────────────

def _call_vision(
    client,
    model: str,
    b64_url: str,
    prompt: str,
    max_tokens: int,
    retry_attempts: int,
    retry_backoff: float,
    extra_body: dict | None = None,
) -> str:
    last_exc: Exception | None = None
    for attempt in range(retry_attempts):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT if prompt is SYSTEM_PROMPT else ""},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": b64_url}},
                            {"type": "text",      "text": prompt},
                        ],
                    },
                ],
                max_tokens=max_tokens,
                temperature=0,
                timeout=180,
                **({"extra_body": extra_body} if extra_body else {}),
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            last_exc = exc
            if attempt < retry_attempts - 1:
                time.sleep(retry_backoff ** attempt)
    raise last_exc  # type: ignore[misc]


def _call_page(
    client, cfg: Config, b64_url: str, is_first: bool
) -> str:
    prompt = (
        "Analyse this document page fully. "
        "Follow the output format in the system prompt exactly."
        if is_first
        else CONTENT_ONLY_PROMPT
    )
    # Qwen3 thinking mode: disable for deterministic extraction
    extra = {"chat_template_kwargs": {"enable_thinking": False}}
    return _call_vision(
        client, cfg.vlm_model, b64_url, prompt,
        cfg.vlm_max_tokens, cfg.vlm_retry_attempts, cfg.vlm_retry_backoff,
        extra_body=extra,
    )


# ── PDF extraction (parallel pages) ──────────────────────────────────────────

def _extract_pdf(client, cfg: Config, path: Path) -> tuple[str, int, int]:
    """Returns (combined_markdown, table_count, page_count)."""
    import pypdfium2 as pdfium

    doc        = pdfium.PdfDocument(str(path))
    page_count = len(doc)
    doc.close()

    # Pre-render all pages (fast, local, no network)
    b64_urls: list[str] = []
    for i in range(page_count):
        b64_urls.append(_pdf_page_to_b64_url(path, i, cfg.vlm_image_dpi))

    # Parallel VLM calls — preserve order via index
    results: list[str] = [""] * page_count
    with ThreadPoolExecutor(max_workers=cfg.vlm_max_workers) as pool:
        futures = {
            pool.submit(_call_page, client, cfg, url, i == 0): i
            for i, url in enumerate(b64_urls)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                print(f"    [vlm] page {idx + 1} error: {exc}")
                results[idx] = f"\n\n> ⚠ Page {idx + 1} extraction failed: {exc}\n\n"

    # Combine pages: first page already has metadata block; subsequent pages
    # get a thin separator
    parts: list[str] = []
    for i, text in enumerate(results):
        if not text.strip():
            continue
        if i > 0:
            parts.append(f"\n\n---\n*Page {i + 1}*\n\n")
        parts.append(text)

    combined    = _strip_bidi("".join(parts))
    table_count = _count_md_tables(combined)
    return combined, table_count, page_count


def _extract_image(client, cfg: Config, path: Path) -> tuple[str, int, int]:
    b64_url = _image_to_b64_url(path)
    text    = _strip_bidi(_call_page(client, cfg, b64_url, is_first=True))
    return text, _count_md_tables(text), 1


# ── Public parse function ─────────────────────────────────────────────────────

def parse(path: Path, cfg: Config) -> ParseResult:
    try:
        import openai
        client = openai.OpenAI(base_url=cfg.vlm_base_url, api_key="none")

        suf = path.suffix.lower()
        if suf == ".pdf":
            content, table_count, page_count = _extract_pdf(client, cfg, path)
        else:
            content, table_count, page_count = _extract_image(client, cfg, path)

        header = (
            f"---\n"
            f"source: {path.name}\n"
            f"parser: vlm\n"
            f"model: {cfg.vlm_model}\n"
            f"pages: {page_count}\n"
            f"---\n\n"
        )

        return ParseResult(
            source=path,
            parser="vlm",
            content=header + content,
            page_count=page_count,
            extras={"table_count": table_count, "model": cfg.vlm_model},
        )

    except Exception as exc:
        return ParseResult(
            source=path, parser="vlm", content="",
            error=str(exc),
        )
