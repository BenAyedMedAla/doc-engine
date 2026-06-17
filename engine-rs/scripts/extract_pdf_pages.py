#!/usr/bin/env python3
"""Extract head+tail pages from a PDF into a new file.

Usage: python extract_pdf_pages.py <src> <dst> <head> <tail>
Stdout: number of pages written.
"""
import sys


def main():
    if len(sys.argv) < 5:
        print("Usage: extract_pdf_pages.py <src> <dst> <head> <tail>", file=sys.stderr)
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]
    head = int(sys.argv[3])
    tail = int(sys.argv[4])

    try:
        import pypdfium2 as pdfium
    except ImportError:
        print("pypdfium2 not installed", file=sys.stderr)
        sys.exit(1)

    doc = pdfium.PdfDocument(src)
    total = len(doc)

    if total <= head + tail:
        pages = list(range(total))
    else:
        pages = list(range(head)) + list(range(total - tail, total))

    new_doc = pdfium.PdfDocument.new()
    new_doc.import_pages(doc, pages=pages)
    new_doc.save(dst)

    print(len(pages))


if __name__ == "__main__":
    main()
