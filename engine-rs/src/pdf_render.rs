use anyhow::{Context, Result};
use base64::{Engine as _, engine::general_purpose};
use pdfium_render::prelude::*;
use std::io::Cursor;
use std::path::Path;

/// Render every page of a PDF to a base64-encoded PNG string.
/// Uses pdfium (same engine as pypdfium2) loaded dynamically at runtime.
pub fn render_pages(path: &Path, dpi: u32, pdfium_path: Option<&str>) -> Result<(Vec<String>, u32)> {
    let pdfium = bind_pdfium(pdfium_path)
        .context("Could not load pdfium library. Set PDFIUM_PATH env var or use --pdfium-path.")?;

    let path_str = path
        .to_str()
        .ok_or_else(|| anyhow::anyhow!("non-UTF8 path: {}", path.display()))?;

    let doc = pdfium
        .load_pdf_from_file(path_str, None)
        .context("Failed to open PDF with pdfium")?;

    let page_count = doc.pages().len() as u32;
    let scale = dpi as f32 / 72.0; // PDF points are 1/72 inch
    let render_cfg = PdfRenderConfig::new().scale_page_by_factor(scale);

    let mut pages_b64 = Vec::with_capacity(page_count as usize);

    for page in doc.pages().iter() {
        let bitmap = page
            .render_with_config(&render_cfg)
            .context("Failed to render PDF page")?;

        let image = bitmap.as_image();
        let mut png_bytes: Vec<u8> = Vec::new();
        image
            .write_to(&mut Cursor::new(&mut png_bytes), image::ImageFormat::Png)
            .context("Failed to encode page as PNG")?;

        pages_b64.push(general_purpose::STANDARD.encode(&png_bytes));
    }

    Ok((pages_b64, page_count))
}

/// Extract head + tail pages from a PDF into a new file using lopdf.
/// Returns the original total page count.
pub fn extract_pages(src: &Path, dst: &Path, head: u32, tail: u32) -> Result<u32> {
    let mut doc = lopdf::Document::load(src)
        .with_context(|| format!("failed to load {}", src.display()))?;

    let total = doc.get_pages().len() as u32;

    if total == 0 {
        anyhow::bail!("PDF has no pages: {}", src.display());
    }

    let keep_head_end = head.min(total);
    let tail_start = if total > tail { total - tail + 1 } else { 1 };

    // Delete every page that falls between the head block and the tail block.
    let to_delete: Vec<u32> = (1..=total)
        .filter(|p| *p > keep_head_end && *p < tail_start)
        .collect();

    if !to_delete.is_empty() {
        doc.delete_pages(&to_delete);
    }

    doc.save(dst)
        .with_context(|| format!("failed to save excerpt to {}", dst.display()))?;

    Ok(total)
}

// ── pdfium binding helpers ────────────────────────────────────────────────────

fn bind_pdfium(explicit_path: Option<&str>) -> Result<Pdfium> {
    // 1. Explicit path from CLI / config
    if let Some(p) = explicit_path {
        return Ok(Pdfium::new(Pdfium::bind_to_library(p)?));
    }

    // 2. PDFIUM_PATH env var
    if let Ok(p) = std::env::var("PDFIUM_PATH") {
        if let Ok(b) = Pdfium::bind_to_library(&p) {
            return Ok(Pdfium::new(b));
        }
    }

    // 3. VIRTUAL_ENV — search inside the active venv's pypdfium2_raw package
    if let Ok(venv) = std::env::var("VIRTUAL_ENV") {
        for candidate in pypdfium2_candidates(&venv) {
            if candidate.exists() {
                let s = candidate.to_string_lossy();
                if let Ok(b) = Pdfium::bind_to_library(s.as_ref()) {
                    return Ok(Pdfium::new(b));
                }
            }
        }
    }

    // 4. System dynamic linker (LD_LIBRARY_PATH / ldconfig)
    Ok(Pdfium::new(Pdfium::bind_to_system_library()?))
}

/// Possible libpdfium.so paths inside a pypdfium2-bearing venv.
fn pypdfium2_candidates(venv: &str) -> Vec<std::path::PathBuf> {
    let mut out = Vec::new();
    for py in ["python3.12", "python3.11", "python3.10", "python3.9"] {
        let base = std::path::PathBuf::from(venv)
            .join("lib")
            .join(py)
            .join("site-packages")
            .join("pypdfium2_raw");
        out.push(base.join("libpdfium.so"));
        out.push(base.join("lib").join("libpdfium.so"));
    }
    out
}
