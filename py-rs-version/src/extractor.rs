/// Long-PDF head+tail page extraction using lopdf.
///
/// Builds a new PDF containing only the first `head` and last `tail` pages
/// of the source document.  Only the selected pages are decoded; the rest
/// of the PDF is never touched.
use std::collections::BTreeSet;
use std::path::Path;

use anyhow::Result;

pub fn extract_pdf_pages(src: &Path, dst: &Path, head: usize, tail: usize) -> Result<usize> {
    let mut doc = lopdf::Document::load(src)?;
    let pages = doc.get_pages();
    let total = pages.len();

    if total <= head + tail {
        // Already short enough — just save as-is (avoids a pointless re-encode)
        doc.save(dst)?;
        return Ok(total);
    }

    let page_keys: Vec<u32> = pages.keys().cloned().collect(); // sorted by BTreeMap

    // Pages to keep (1-indexed, matching lopdf's numbering)
    let keep: BTreeSet<u32> = page_keys[..head]
        .iter()
        .chain(page_keys[total - tail..].iter())
        .cloned()
        .collect();

    let to_delete: Vec<u32> = page_keys
        .into_iter()
        .filter(|p| !keep.contains(p))
        .collect();

    doc.delete_pages(&to_delete);
    doc.save(dst)?;

    Ok(keep.len())
}
