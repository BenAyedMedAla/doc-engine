#!/usr/bin/env python3
"""Render all pages of a PDF to base64-encoded PNG images.

Usage: python render_pdf.py <pdf_path> <dpi>
Stdout: JSON array of base64 strings, one element per page.
"""
import sys
import json
import base64
import io


def main():
    if len(sys.argv) < 3:
        print("Usage: render_pdf.py <pdf_path> <dpi>", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    dpi = int(sys.argv[2])

    try:
        import pypdfium2 as pdfium
    except ImportError:
        print("pypdfium2 not installed", file=sys.stderr)
        sys.exit(1)

    doc = pdfium.PdfDocument(pdf_path)
    results = []

    for i in range(len(doc)):
        page = doc[i]
        scale = dpi / 72.0  # pypdfium2 uses 72 DPI as the base unit
        bitmap = page.render(scale=scale, rotation=0)
        pil_image = bitmap.to_pil()

        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        results.append(b64)

    print(json.dumps(results))


if __name__ == "__main__":
    main()
