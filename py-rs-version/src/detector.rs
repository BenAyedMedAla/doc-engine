/// Fast document classification — zero page rendering, zero heavy parsing.
///
/// PDF page count: reads the page tree /Count entry via lopdf (O(1)).
/// Scanned detection: samples N evenly-spaced pages and measures average
/// characters from the embedded text layer.  A real text PDF has hundreds
/// of chars per page; a scanned/image-only PDF typically has < 10.
use std::path::Path;

use crate::config::Config;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum DocClass {
    Office,
    Image,
    PdfVlmText,    // ≤ vlm_text_threshold pages, text-native → VLM
    PdfShortText,  // (vlm_text_threshold, long_pdf_threshold], text → Docling
    PdfShortScan,  // ≤ scanned_long_threshold pages, scanned → VLM
    PdfLongText,   // > long_pdf_threshold pages, text → VLM head+tail
    PdfLongScan,   // > scanned_long_threshold pages, scanned → VLM head+tail
    Unknown,
}

impl DocClass {
    /// Subdirectory under sorted/ for this class.
    pub fn subdir(&self) -> Option<&'static str> {
        match self {
            DocClass::Office       => Some("office"),
            DocClass::Image        => Some("images"),
            DocClass::PdfVlmText   => Some("pdfs/vlm_text"),
            DocClass::PdfShortText => Some("pdfs/short_text"),
            DocClass::PdfShortScan => Some("pdfs/short_scanned"),
            DocClass::PdfLongText  => Some("pdfs/long_text"),
            DocClass::PdfLongScan  => Some("pdfs/long_scanned"),
            DocClass::Unknown      => None,
        }
    }

    pub fn label(&self) -> &'static str {
        match self {
            DocClass::Office       => "office",
            DocClass::Image        => "image",
            DocClass::PdfVlmText   => "vlm_text",
            DocClass::PdfShortText => "short_text",
            DocClass::PdfShortScan => "short_scanned",
            DocClass::PdfLongText  => "long_text",
            DocClass::PdfLongScan  => "long_scanned",
            DocClass::Unknown      => "unknown",
        }
    }

    /// Which Python parser script handles this class.
    pub fn parser_script(&self) -> &'static str {
        match self {
            DocClass::Office => "office_parser.py",
            DocClass::PdfShortText => "docling_parser.py",
            _ => "vlm_parser.py",
        }
    }
}

const OFFICE_EXTS: &[&str] = &[
    "docx", "doc", "odt", "rtf",
    "xlsx", "xls", "ods",
    "pptx", "ppt", "odp",
];

const IMAGE_EXTS: &[&str] = &[
    "png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp",
];

// ── PDF introspection ─────────────────────────────────────────────────────────

pub fn pdf_page_count(path: &Path) -> usize {
    match lopdf::Document::load(path) {
        Ok(doc) => doc.get_pages().len(),
        Err(_)  => 0,
    }
}

/// Returns true when the average extracted text per sampled page is below
/// `threshold` characters — the signature of a scanned/image-only PDF.
///
/// Pages are sampled evenly across the whole document so a report with a
/// scanned cover + text body is classified correctly.
pub fn pdf_is_scanned(path: &Path, sample: usize, threshold: usize) -> bool {
    let doc = match lopdf::Document::load(path) {
        Ok(d)  => d,
        Err(_) => return false, // assume text-native on load error
    };

    let pages = doc.get_pages();
    let total = pages.len();
    if total == 0 {
        return true;
    }

    // BTreeMap keys are always sorted — use that ordering for even spacing
    let page_keys: Vec<u32> = pages.keys().cloned().collect();
    let n = sample.min(total);
    let sampled: Vec<u32> = (0..n).map(|i| page_keys[i * total / n]).collect();

    let mut total_chars: usize = 0;
    let mut counted: usize = 0;

    for &pnum in &sampled {
        if let Ok(text) = doc.extract_text(&[pnum]) {
            total_chars += text.chars().count();
            counted += 1;
        }
    }

    if counted == 0 {
        return false; // extraction failed → treat as text-native (safer)
    }
    (total_chars / counted) < threshold
}

// ── File classification ───────────────────────────────────────────────────────

pub fn classify(path: &Path, cfg: &Config) -> DocClass {
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_lowercase();

    if OFFICE_EXTS.contains(&ext.as_str()) {
        return DocClass::Office;
    }
    if IMAGE_EXTS.contains(&ext.as_str()) {
        return DocClass::Image;
    }
    if ext == "pdf" {
        let pages = pdf_page_count(path);
        if pages == 0 {
            return DocClass::Unknown;
        }
        let scanned = pdf_is_scanned(path, cfg.scan_sample_pages, cfg.scan_char_threshold);
        return if scanned {
            if pages > cfg.scanned_long_threshold {
                DocClass::PdfLongScan
            } else {
                DocClass::PdfShortScan
            }
        } else if pages <= cfg.vlm_text_threshold {
            DocClass::PdfVlmText
        } else if pages > cfg.long_pdf_threshold {
            DocClass::PdfLongText
        } else {
            DocClass::PdfShortText
        };
    }

    DocClass::Unknown
}
