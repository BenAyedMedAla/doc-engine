use std::path::{Path, PathBuf};
use anyhow::Result;
use lopdf::Document;
use crate::config::Config;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum DocClass {
    Office,
    Image,
    PdfVlmText,
    PdfShortText,
    PdfShortScan,
    PdfLongText,
    PdfLongScan,
    Unknown,
}

impl DocClass {
    pub fn as_str(&self) -> &'static str {
        match self {
            DocClass::Office => "office",
            DocClass::Image => "image",
            DocClass::PdfVlmText => "pdf_vlm_text",
            DocClass::PdfShortText => "pdf_short_text",
            DocClass::PdfShortScan => "pdf_short_scan",
            DocClass::PdfLongText => "pdf_long_text",
            DocClass::PdfLongScan => "pdf_long_scan",
            DocClass::Unknown => "unknown",
        }
    }

    /// Subdirectory under sorted/ for this class.
    pub fn sorted_subdir(&self) -> Option<&'static str> {
        match self {
            DocClass::Office => Some("office"),
            DocClass::Image => Some("images"),
            DocClass::PdfVlmText => Some("pdfs/vlm_text"),
            DocClass::PdfShortText => Some("pdfs/short_text"),
            DocClass::PdfShortScan => Some("pdfs/short_scanned"),
            DocClass::PdfLongText => Some("pdfs/long_text"),
            DocClass::PdfLongScan => Some("pdfs/long_scanned"),
            DocClass::Unknown => None,
        }
    }
}

#[derive(Debug, Clone)]
pub struct PdfInfo {
    pub page_count: u32,
    pub is_scanned: bool,
}

const OFFICE_EXTENSIONS: &[&str] = &[
    "docx", "doc", "odt", "rtf",
    "xlsx", "xls", "ods",
    "pptx", "ppt", "odp",
];

const IMAGE_EXTENSIONS: &[&str] = &[
    "png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp",
];

/// O(1) page count via lopdf XRef catalog.
pub fn pdf_page_count(path: &Path) -> u32 {
    Document::load(path)
        .map(|doc| doc.get_pages().len() as u32)
        .unwrap_or(0)
}

/// Sample evenly-spaced pages and measure avg chars to detect scanned PDFs.
/// Mirrors Python: sample_indices = [int(i * total / n) for i in range(n)]
pub fn pdf_is_scanned(path: &Path, sample: usize, threshold: u32) -> bool {
    let doc = match Document::load(path) {
        Ok(d) => d,
        Err(_) => return false,
    };
    let total = doc.get_pages().len();
    if total == 0 {
        return false;
    }
    let n = sample.min(total);
    let mut total_chars = 0usize;
    let mut pages_sampled = 0usize;

    for i in 0..n {
        // 0-indexed sample position, converted to 1-indexed for lopdf
        let page_1idx = (i * total / n + 1) as u32;
        if let Ok(text) = doc.extract_text(&[page_1idx]) {
            total_chars += text.chars().count();
            pages_sampled += 1;
        }
    }

    if pages_sampled == 0 {
        return false;
    }
    (total_chars / pages_sampled) < threshold as usize
}

pub fn analyze_pdf(path: &Path, cfg: &Config) -> PdfInfo {
    PdfInfo {
        page_count: pdf_page_count(path),
        is_scanned: pdf_is_scanned(path, cfg.scan_sample_pages, cfg.scan_char_threshold),
    }
}

pub fn classify(path: &Path, cfg: &Config) -> DocClass {
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_lowercase();

    if OFFICE_EXTENSIONS.contains(&ext.as_str()) {
        return DocClass::Office;
    }
    if IMAGE_EXTENSIONS.contains(&ext.as_str()) {
        return DocClass::Image;
    }
    if ext == "pdf" {
        let info = analyze_pdf(path, cfg);
        return if info.is_scanned {
            if info.page_count <= cfg.scanned_long_threshold {
                DocClass::PdfShortScan
            } else {
                DocClass::PdfLongScan
            }
        } else if info.page_count <= cfg.vlm_text_threshold {
            DocClass::PdfVlmText
        } else if info.page_count <= cfg.long_pdf_threshold {
            DocClass::PdfShortText
        } else {
            DocClass::PdfLongText
        };
    }
    DocClass::Unknown
}

/// Extract head + tail pages into a new PDF using lopdf (pure Rust, no subprocess).
pub fn extract_pdf_pages(src: &Path, dst: &Path, head: u32, tail: u32) -> Result<u32> {
    crate::pdf_render::extract_pages(src, dst, head, tail)
}

/// Locate the scripts/ directory. Walks up from the binary to find it,
/// so it works whether the binary lives in target/release/ or next to scripts/.
pub fn scripts_dir() -> PathBuf {
    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.as_path();
        while let Some(parent) = dir.parent() {
            let candidate = parent.join("scripts");
            if candidate.is_dir() {
                return candidate;
            }
            dir = parent;
        }
    }
    PathBuf::from("scripts")
}

pub fn python_cmd() -> &'static str {
    if cfg!(windows) { "python" } else { "python3" }
}
