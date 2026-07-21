#!/usr/bin/env python3
"""
Fast document classification — zero page rendering, zero heavy parsing.

PDF classification uses only pypdfium2's XRef metadata reader:
  - page_count: O(1) — reads the /Count entry in the PDF catalog
  - is_scanned: samples N evenly-spaced pages and measures avg chars from the
    embedded text layer.  A real text PDF has hundreds of chars/page;
    a scanned/image-only PDF typically has < 10.
"""
from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

from config import OFFICE_EXTENSIONS, IMAGE_EXTENSIONS, Config


class DocClass(Enum):
    OFFICE          = auto()   # DOCX / XLSX / PPTX → Kreuzberg
    IMAGE           = auto()   # PNG / JPG / … → VLM
    PDF_VLM_TEXT    = auto()   # ≤ vlm_text_threshold pages (4), text → VLM
    PDF_SHORT_TEXT  = auto()   # (4, 200] pages, text → Docling
    PDF_SHORT_SCAN  = auto()   # ≤ scanned_long_threshold pages (20), scanned → VLM
    PDF_LONG_TEXT   = auto()   # > long_pdf_threshold pages (200), text → VLM (head+tail)
    PDF_LONG_SCAN   = auto()   # > scanned_long_threshold pages (20), scanned → VLM (head+tail)
    UNKNOWN         = auto()


class PdfInfo(NamedTuple):
    page_count: int
    is_scanned: bool


# ── PDF introspection ─────────────────────────────────────────────────────────

def pdf_page_count(path: Path) -> int:
    """
    Return page count via 3 escalating strategies:
    1. pypdfium2 XRef /Count  — O(1), works on well-formed PDFs
    2. PyMuPDF (fitz)         — repairs damaged XRef, handles incremental saves
    3. Brute-force iteration  — walks pages one by one until failure
    Returns 0 only when all three fail (truly unreadable / encrypted).
    """
    # Strategy 1: pypdfium2 XRef read
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(path))
        n = len(doc)
        doc.close()
        if n > 0:
            return n
    except Exception:
        pass

    # Strategy 2: PyMuPDF — robust repair heuristics, handles stale /Count
    try:
        import fitz
        doc = fitz.open(str(path))
        n = doc.page_count
        doc.close()
        if n > 0:
            return n
    except Exception:
        pass

    # Strategy 3: brute-force — iterate pages until one fails
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(path))
        n = 0
        for i in range(9999):
            try:
                _ = doc[i]
                n += 1
            except Exception:
                break
        doc.close()
        if n > 0:
            return n
    except Exception:
        pass

    return 0


def pdf_is_scanned(path: Path, sample: int = 5, threshold: int = 50) -> bool:
    """
    Return True when the average extracted text per sampled page is below
    `threshold` characters — the signature of a scanned/image-only PDF.

    Pages are sampled evenly across the document (not just from the front)
    so a report with a scanned cover + text body is handled correctly.
    Does NOT render any page pixels.
    """
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(path))
        total = len(doc)
        if total == 0:
            doc.close()
            return True

        n = min(sample, total)
        # Evenly spread indices: 0, total/n, 2*total/n, …
        indices = sorted({int(i * total / n) for i in range(n)})
        char_counts = [len(doc[i].get_textpage().get_text_range()) for i in indices]
        doc.close()
        return (sum(char_counts) / len(char_counts)) < threshold
    except Exception:
        return False  # assume text-native on error (safer — won't over-VLM)


def analyze_pdf(path: Path, cfg: Config) -> PdfInfo:
    pages   = pdf_page_count(path)
    scanned = pdf_is_scanned(path, sample=cfg.scan_sample_pages,
                             threshold=cfg.scan_char_threshold)
    return PdfInfo(page_count=pages, is_scanned=scanned)


# ── File classification ───────────────────────────────────────────────────────

def classify(path: Path, cfg: Config) -> DocClass:
    suf = path.suffix.lower()

    if suf in OFFICE_EXTENSIONS:
        return DocClass.OFFICE

    if suf in IMAGE_EXTENSIONS:
        return DocClass.IMAGE

    if suf == ".pdf":
        info = analyze_pdf(path, cfg)
        if info.page_count == 0:
            return DocClass.UNKNOWN
        if info.is_scanned:
            if info.page_count > cfg.scanned_long_threshold:
                return DocClass.PDF_LONG_SCAN
            return DocClass.PDF_SHORT_SCAN
        else:
            if info.page_count <= cfg.vlm_text_threshold:
                return DocClass.PDF_VLM_TEXT
            if info.page_count > cfg.long_pdf_threshold:
                return DocClass.PDF_LONG_TEXT
            return DocClass.PDF_SHORT_TEXT

    return DocClass.UNKNOWN


# ── Long-PDF page extraction ──────────────────────────────────────────────────

def extract_pdf_pages(src: Path, dst: Path, head: int = 10, tail: int = 10) -> int:
    """
    Write first `head` + last `tail` pages of `src` into a new PDF at `dst`.
    Uses pypdfium2's import_pages — only the selected pages are decoded.

    Returns the number of pages written.
    """
    import pypdfium2 as pdfium

    doc   = pdfium.PdfDocument(str(src))
    total = len(doc)

    if total <= head + tail:
        # Already short enough — copy all pages
        pages = list(range(total))
    else:
        pages = list(range(head)) + list(range(total - tail, total))
        pages = sorted(set(pages))

    new_doc = pdfium.PdfDocument.new()
    new_doc.import_pages(doc, pages=pages)
    new_doc.save(str(dst))
    new_doc.close()
    doc.close()
    return len(pages)
