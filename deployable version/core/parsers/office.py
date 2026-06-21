from __future__ import annotations

import logging
import os
import re
from pathlib import Path

# Must be set before kreuzberg imports (ORT is loaded at import time).
# Kreuzberg's ONNX Runtime aborts on Blackwell (sm_120) at the C++ boundary;
# forcing CPU execution keeps it stable.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

from . import ParseResult

logger = logging.getLogger(__name__)

_BIDI = re.compile(r"[\u200E\u200F\u202A-\u202E\u2066-\u2069؜﻿]")
_GARBAGE_RE = re.compile(
    r"[^\x01-ɏ؀-ۿݐ-ݿࢠ-ࣿ"
    r" -⁯\s]"
)


def _strip_bidi(text: str) -> str:
    return _BIDI.sub("", text)


def _garbage_ratio(text: str) -> float:
    if not text:
        return 0.0
    return len(_GARBAGE_RE.findall(text)) / len(text)


def _render_table(content: dict) -> str:
    grid  = content.get("grid", {})
    cells = grid.get("cells", [])
    rows, cols = grid.get("rows", 0), grid.get("cols", 0)
    if not (cells and rows and cols):
        return ""
    table: list[list[str]] = [[""] * cols for _ in range(rows)]
    for cell in cells:
        r, c = cell.get("row", 0), cell.get("col", 0)
        if r < rows and c < cols:
            table[r][c] = (
                cell.get("content", "").replace("|", r"\|").replace("\n", " ")
            )
    lines: list[str] = []
    for i, row in enumerate(table):
        lines.append("| " + " | ".join(row) + " |")
        if i == 0:
            lines.append("| " + " | ".join("---" for _ in row) + " |")
    return "\n".join(lines)


def _render_nodes(nodes: list, indices: list[int], depth: int = 0) -> str:
    if depth > 30:
        return ""
    parts: list[str] = []
    for idx in indices:
        if idx >= len(nodes):
            continue
        n        = nodes[idx]
        content  = n.get("content", {})
        nt       = content.get("node_type", "")
        children = n.get("children", [])

        if nt == "paragraph":
            text = content.get("text", "").strip()
            if text:
                parts.append(text)

        elif nt == "heading":
            text  = (content.get("heading_text") or content.get("text", "")).strip()
            level = content.get("heading_level", 2)
            if text:
                parts.append("#" * level + " " + text)

        elif nt == "group":
            heading = (content.get("heading_text") or "").strip()
            level   = content.get("heading_level", 2)
            if heading:
                parts.append("#" * level + " " + heading)
            non_heading = [
                c for c in children
                if c < len(nodes)
                and nodes[c].get("content", {}).get("node_type") != "heading"
            ]
            sub = _render_nodes(nodes, non_heading, depth + 1)
            if sub:
                parts.append(sub)

        elif nt == "list":
            sub = _render_nodes(nodes, children, depth + 1)
            if sub:
                parts.append(sub)

        elif nt == "list_item":
            text = content.get("text", "").strip()
            if text:
                parts.append("- " + text)

        elif nt == "table":
            md = _render_table(content)
            if md:
                parts.append(md)

    return "\n\n".join(p for p in parts if p)


def _render_document(doc: dict | None, fallback: str) -> str:
    if not doc or not isinstance(doc, dict):
        return fallback
    nodes = doc.get("nodes", [])
    if not nodes:
        return fallback
    all_children: set[int] = set()
    for node in nodes:
        all_children.update(node.get("children", []))
    roots    = [i for i in range(len(nodes)) if i not in all_children]
    rendered = _render_nodes(nodes, roots)
    return _strip_bidi(rendered) if rendered.strip() else fallback


_KREUZBERG_CONFIGS = None


def _build_kreuzberg_configs():
    import kreuzberg

    tess = kreuzberg.TesseractConfig(
        language="ara+eng",
        oem=1,
        psm=3,
        min_confidence=0.3,
    )
    ocr    = kreuzberg.OcrConfig(backend="tesseract", tesseract_config=tess)
    layout = kreuzberg.LayoutDetectionConfig(
        apply_heuristics=True,
        table_model="tatr",
        confidence_threshold=0.5,
    )
    acc  = kreuzberg.AccelerationConfig(provider="cpu")
    pdf  = kreuzberg.PdfConfig(allow_single_column_tables=True, extract_metadata=True)
    lang = kreuzberg.LanguageDetectionConfig(enabled=True, detect_multiple=True, min_confidence=0.5)

    base       = dict(ocr=ocr, layout=layout, acceleration=acc,
                      include_document_structure=True, pdf_options=pdf, language_detection=lang)
    cfg_normal = kreuzberg.ExtractionConfig(**base)
    cfg_force  = kreuzberg.ExtractionConfig(**base, force_ocr=True)
    return cfg_normal, cfg_force


def _get_configs():
    global _KREUZBERG_CONFIGS
    if _KREUZBERG_CONFIGS is None:
        _KREUZBERG_CONFIGS = _build_kreuzberg_configs()
    return _KREUZBERG_CONFIGS


def _make_header(path: Path, parser: str, pages: int | None, langs) -> str:
    lang_str  = ""
    if langs:
        try:
            lang_str = f"\nlanguages: {', '.join(str(l) for l in langs)}"
        except Exception:
            pass
    pages_str = f"\npages: {pages}" if pages is not None else ""
    return f"---\nsource: {path.name}\nparser: {parser}{pages_str}{lang_str}\n---\n\n"


def parse(path: Path) -> ParseResult:
    try:
        import kreuzberg

        cfg_normal, cfg_force = _get_configs()

        r    = kreuzberg.extract_file_sync(str(path), config=cfg_normal)
        flat = _strip_bidi(getattr(r, "content", "") or "")

        if _garbage_ratio(flat) > 0.02:
            logger.info("Garbage detected in %s — retrying with force_ocr", path.name)
            r    = kreuzberg.extract_file_sync(str(path), config=cfg_force)
            flat = _strip_bidi(getattr(r, "content", "") or "")

        doc  = getattr(r, "document", None)
        text = _render_document(doc, flat)

        tables = getattr(r, "tables", None) or []
        langs  = getattr(r, "detected_languages", None)

        try:
            pages = r.get_page_count()
        except Exception:
            pages = None

        header = _make_header(path, "kreuzberg", pages, langs)
        return ParseResult(
            source=path,
            parser="kreuzberg",
            content=header + text,
            page_count=pages,
            extras={"detected_languages": langs, "table_count": len(tables)},
        )

    except Exception as exc:
        logger.exception("Kreuzberg failed for %s", path.name)
        return ParseResult(source=path, parser="kreuzberg", content="", error=str(exc))
