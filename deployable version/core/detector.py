from __future__ import annotations

import logging
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

from .config import OFFICE_EXTENSIONS, IMAGE_EXTENSIONS, Config

logger = logging.getLogger(__name__)


class DocClass(Enum):
    OFFICE          = auto()   # DOCX / XLSX / PPTX → Kreuzberg
    IMAGE           = auto()   # PNG / JPG / … → VLM
    PDF_VLM_TEXT    = auto()   # ≤ vlm_text_threshold pages, text → VLM
    PDF_SHORT_TEXT  = auto()   # (threshold, long_threshold] pages, text → Docling
    PDF_SHORT_SCAN  = auto()   # ≤ scanned_long_threshold pages, scanned → VLM
    PDF_LONG_TEXT   = auto()   # > long_threshold pages, text → VLM (head+tail)
    PDF_LONG_SCAN   = auto()   # > scanned_long_threshold pages, scanned → VLM (head+tail)
    UNKNOWN         = auto()


class PdfInfo(NamedTuple):
    page_count: int
    is_scanned: bool


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

    logger.warning("Could not determine page count for %s after all fallbacks", path.name)
    return 0


def pdf_is_scanned(path: Path, sample: int = 5, threshold: int = 50) -> bool:
    """
    Return True when the average extracted text per sampled page is below
    threshold — the signature of a scanned/image-only PDF.
    Pages are sampled evenly across the document so a report with a scanned
    cover + text body is handled correctly.
    """
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(path))
        total = len(doc)
        if total == 0:
            doc.close()
            return True
        n = min(sample, total)
        indices = sorted({int(i * total / n) for i in range(n)})
        char_counts = [len(doc[i].get_textpage().get_text_range()) for i in indices]
        doc.close()
        return (sum(char_counts) / len(char_counts)) < threshold
    except Exception:
        return False  # assume text-native on error — safer, won't over-VLM


def analyze_pdf(path: Path, cfg: Config) -> PdfInfo:
    pages   = pdf_page_count(path)
    scanned = pdf_is_scanned(path, sample=cfg.scan_sample_pages,
                             threshold=cfg.scan_char_threshold)
    return PdfInfo(page_count=pages, is_scanned=scanned)


def classify(path: Path, cfg: Config) -> DocClass:
    suf = path.suffix.lower()

    if suf in OFFICE_EXTENSIONS:
        return DocClass.OFFICE

    if suf in IMAGE_EXTENSIONS:
        return DocClass.IMAGE

    if suf == ".pdf":
        info = analyze_pdf(path, cfg)
        if info.page_count == 0:
            logger.warning("Unreadable PDF (encrypted or corrupted): %s", path.name)
            return DocClass.UNKNOWN
        if info.is_scanned:
            return (DocClass.PDF_LONG_SCAN
                    if info.page_count > cfg.scanned_long_threshold
                    else DocClass.PDF_SHORT_SCAN)
        else:
            if info.page_count <= cfg.vlm_text_threshold:
                return DocClass.PDF_VLM_TEXT
            if info.page_count > cfg.long_pdf_threshold:
                return DocClass.PDF_LONG_TEXT
            return DocClass.PDF_SHORT_TEXT

    return DocClass.UNKNOWN


def extract_pdf_pages(src: Path, dst: Path, head: int = 10, tail: int = 10) -> int:
    """Write first `head` + last `tail` pages of `src` into a new PDF at `dst`."""
    import pypdfium2 as pdfium

    doc   = pdfium.PdfDocument(str(src))
    total = len(doc)

    if total <= head + tail:
        pages = list(range(total))
    else:
        pages = sorted(set(list(range(head)) + list(range(total - tail, total))))

    new_doc = pdfium.PdfDocument.new()
    new_doc.import_pages(doc, pages=pages)
    new_doc.save(str(dst))
    new_doc.close()
    doc.close()
    return len(pages)
