#!/usr/bin/env python3
"""
Docling parser — text-native PDFs → structured Markdown.
Invoked as a subprocess by pipeline.py.

By the time a file reaches this parser it is already classified as
text-native, so OCR is disabled by default.  TableFormer ACCURATE
mode runs on GPU when available.

Usage:
  python3 docling_parser.py --input <file> --output-dir <dir>

Prints one JSON line to stdout on completion (read by the orchestrator).
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from common import ParseResult

# ── Unicode helpers ───────────────────────────────────────────────────────────

_BIDI = re.compile(r"[\u200E\u200F\u202A-\u202E\u2066-\u2069؜﻿]")

_VALID_RANGES = [
    (0x0000, 0x024F),
    (0x0300, 0x036F),
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0x2000, 0x206F),
]


def _strip_bidi(text: str) -> str:
    return _BIDI.sub("", text)


def _garbage_ratio(text: str) -> float:
    if not text:
        return 0.0
    bad = sum(
        1 for c in text
        if not any(lo <= ord(c) <= hi for lo, hi in _VALID_RANGES)
        and not c.isspace()
    )
    return bad / len(text)


def _arabic_pf_ratio(text: str) -> float:
    """Fraction of Arabic chars that are Presentation Forms (old visual encoding)."""
    pf = sum(
        1 for c in text
        if 0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFF
    )
    total_arabic = sum(
        1 for c in text
        if (0x0600 <= ord(c) <= 0x06FF
            or 0x0750 <= ord(c) <= 0x077F
            or 0x08A0 <= ord(c) <= 0x08FF
            or 0xFB50 <= ord(c) <= 0xFDFF
            or 0xFE70 <= ord(c) <= 0xFEFF)
    )
    return pf / total_arabic if total_arabic > 10 else 0.0


def _nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


# ── GPU probe ─────────────────────────────────────────────────────────────────

def _get_accelerator():
    try:
        import torch
        if not torch.cuda.is_available():
            return None
        probe = torch.ones(1, device="cuda")
        _ = (probe + 1).sum().item()
        del probe
        from docling.datamodel.pipeline_options import AcceleratorOptions, AcceleratorDevice
        return AcceleratorOptions(device=AcceleratorDevice.CUDA)
    except Exception:
        return None


# ── OCR backend (only for Arabic Presentation Form fallback) ──────────────────

def _pick_ocr_options(*, use_gpu: bool):
    """
    use_gpu=False is required for the CPU-fallback pipeline: EasyOcrOptions
    with use_gpu=True will try CUDA internally even when attached to the CPU
    PdfPipelineOptions, which defeats the whole point of falling back (an
    OOM'd GPU conversion would just OOM a second time inside "CPU" OCR).
    """
    try:
        import easyocr  # noqa
        from docling.datamodel.pipeline_options import EasyOcrOptions
        attempts = (
            [{"lang": ["ar", "en"], "use_gpu": True}, {"lang": ["ar", "en"]}]
            if use_gpu else
            [{"lang": ["ar", "en"], "use_gpu": False}]
        )
        for kwargs in attempts:
            try:
                return EasyOcrOptions(**kwargs)
            except Exception:
                continue
    except ImportError:
        pass

    import shutil
    tess = shutil.which("tesseract")
    if tess:
        from docling.datamodel.pipeline_options import TesseractCliOcrOptions
        for kwargs in [
            {"lang": ["ara", "eng"], "tesseract_cmd": tess, "psm": 3, "oem": 1},
            {"lang": ["ara", "eng"], "tesseract_cmd": tess, "psm": 3},
        ]:
            try:
                return TesseractCliOcrOptions(**kwargs)
            except Exception:
                continue

    if not use_gpu:
        return None

    try:
        from docling.datamodel.pipeline_options import RapidOcrOptions
        return RapidOcrOptions()
    except Exception:
        pass

    return None


# ── Converter singleton ───────────────────────────────────────────────────────

_CONVERTERS: dict | None = None


def _build_converters() -> dict:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions, TableStructureOptions, TableFormerMode,
    )

    acc      = _get_accelerator()
    on_gpu   = acc is not None
    # Re-tuned for a 23 GB L4 (was 8/4/4, sized for a 97 GB RTX PRO 6000).
    # Docling runs concurrently with a resident vLLM process on this same GPU
    # (pipeline.py's _DOCLING_SLOTS/_VLM_SLOTS), so it only gets a slice of VRAM.
    layout_bs = 2 if on_gpu else 1
    table_bs  = 2 if on_gpu else 1
    ocr_bs    = 2 if on_gpu else 1
    # Separate OCR option objects for the GPU and CPU pipelines — the CPU
    # fallback must not carry a GPU-enabled EasyOCR backend, or an OOM'd GPU
    # conversion just OOMs a second time "inside" the CPU fallback.
    ocr_opts_gpu = _pick_ocr_options(use_gpu=True)
    ocr_opts_cpu = _pick_ocr_options(use_gpu=False)
    table_opts = TableStructureOptions(mode=TableFormerMode.ACCURATE)

    def _pipe(*, do_ocr: bool, force_ocr: bool = False) -> PdfPipelineOptions:
        kw: dict = dict(
            do_ocr=do_ocr,
            do_table_structure=True,
            images_scale=3.0,
            layout_batch_size=layout_bs,
            table_batch_size=table_bs,
            table_structure_options=table_opts,
            document_timeout=600,
        )
        if do_ocr and ocr_opts_gpu is not None:
            kw["ocr_options"]    = ocr_opts_gpu
            kw["ocr_batch_size"] = ocr_bs
        if force_ocr:
            kw["force_full_page_ocr"] = True
        if acc is not None:
            try:
                return PdfPipelineOptions(**kw, accelerator_options=acc)
            except TypeError:
                pass
        return PdfPipelineOptions(**kw)

    def _conv(pipe):
        return DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipe),
        })

    # CPU fallback (used on CUDA OOM or CUDA errors) — genuinely CPU-only,
    # including its OCR backend. Docling auto-detects CUDA is available
    # system-wide regardless of what we pass here, so accelerator_options
    # must be explicitly forced to CPU — merely omitting it is not enough
    # (that was the original bug: the "CPU" pipeline still tried CUDA and
    # OOM'd a second time after the GPU pipeline already OOM'd once).
    from docling.datamodel.pipeline_options import AcceleratorOptions, AcceleratorDevice
    cpu_acc = AcceleratorOptions(device=AcceleratorDevice.CPU)

    def _pipe_cpu(*, do_ocr: bool, force_ocr: bool = False) -> PdfPipelineOptions:
        kw: dict = dict(
            do_ocr=do_ocr, do_table_structure=True, images_scale=3.0,
            layout_batch_size=1, table_batch_size=1,
            table_structure_options=table_opts, document_timeout=600,
            accelerator_options=cpu_acc,
        )
        if do_ocr and ocr_opts_cpu is not None:
            kw["ocr_options"] = ocr_opts_cpu
        if force_ocr:
            kw["force_full_page_ocr"] = True
        return PdfPipelineOptions(**kw)

    print(
        f"  [docling] GPU={on_gpu} | tables=ACCURATE | "
        f"batches=layout{layout_bs}/tbl{table_bs}",
        file=sys.stderr,
    )

    return {
        "native":    (_conv(_pipe(do_ocr=False)),      _conv(_pipe_cpu(do_ocr=False))),
        "force_ocr": (_conv(_pipe(do_ocr=True, force_ocr=True)),
                      _conv(_pipe_cpu(do_ocr=True, force_ocr=True))),
        "on_gpu":    on_gpu,
    }


def _get_converters() -> dict:
    global _CONVERTERS
    if _CONVERTERS is None:
        _CONVERTERS = _build_converters()
    return _CONVERTERS


def _convert(conv_pair, path: Path):
    gpu_conv, cpu_conv = conv_pair
    if not _get_converters()["on_gpu"]:
        return cpu_conv.convert(str(path)), False
    try:
        result = gpu_conv.convert(str(path))
        try:
            import torch; torch.cuda.empty_cache()
        except Exception:
            pass
        return result, False
    except Exception as e:
        # Any GPU-path failure falls back to CPU rather than only specific
        # CUDA/OOM substrings — the GPU is shared with a resident vLLM process
        # on this box, so contention can surface as many different error types.
        print(f"  [docling] GPU conversion failed ({e!r}) — falling back to CPU", file=sys.stderr)
        try:
            import torch; torch.cuda.empty_cache()
        except Exception:
            pass
        return cpu_conv.convert(str(path)), True


# ── Parser ────────────────────────────────────────────────────────────────────

def parse(path: Path) -> ParseResult:
    try:
        convs = _get_converters()

        result, used_cpu = _convert(convs["native"], path)
        doc  = result.document
        text = _strip_bidi(doc.export_to_text() or "")

        # Reassign used_cpu (not discard it) — whichever conversion actually
        # produced the `doc` we go on to use is the one whose GPU/CPU status
        # must be reported, or "gpu: True" can end up on output that was
        # really recovered via the CPU fallback.
        if _garbage_ratio(text) > 0.01:
            result, used_cpu = _convert(convs["force_ocr"], path)
            doc  = result.document
            text = _strip_bidi(doc.export_to_text() or "")
        elif _arabic_pf_ratio(text) > 0.3:
            result, used_cpu = _convert(convs["force_ocr"], path)
            doc  = result.document
            text = _strip_bidi(doc.export_to_text() or "")

        text = _nfkc(text)
        md   = _nfkc(_strip_bidi(doc.export_to_markdown() or text))

        tables     = getattr(doc, "tables", None) or []
        page_count = len(getattr(doc, "pages", None) or []) or None

        header = (
            f"---\n"
            f"source: {path.name}\n"
            f"parser: docling\n"
            f"{'pages: ' + str(page_count) + chr(10) if page_count else ''}"
            f"gpu: {_get_converters()['on_gpu'] and not used_cpu}\n"
            f"---\n\n"
        )

        return ParseResult(
            source=path, parser="docling",
            content=header + md, page_count=page_count,
            extras={"table_count": len(tables), "gpu": not used_cpu, "cpu_fallback": used_cpu},
        )

    except Exception as exc:
        return ParseResult(source=path, parser="docling", content="", error=str(exc))


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input",      type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()

    result = parse(args.input)
    if result.ok:
        result.save(args.output_dir)
    result.emit()


if __name__ == "__main__":
    main()
