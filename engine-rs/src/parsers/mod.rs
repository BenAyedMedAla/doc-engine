pub mod docling;
pub mod office;
pub mod vlm;

use std::ffi::OsString;
use std::path::{Path, PathBuf};
use anyhow::Result;

#[derive(Debug, Clone)]
pub struct ParseResult {
    pub source: PathBuf,
    pub parser: String,
    pub content: String,
    pub page_count: Option<u32>,
    pub extras: serde_json::Value,
    pub error: Option<String>,
}

impl ParseResult {
    pub fn ok(&self) -> bool {
        self.error.is_none()
    }

    pub fn error_result(source: PathBuf, parser: &str, error: String) -> Self {
        Self {
            source,
            parser: parser.to_string(),
            content: String::new(),
            page_count: None,
            extras: serde_json::Value::Object(Default::default()),
            error: Some(error),
        }
    }

    /// Write content to `<output_dir>/<stem>.md`, deduplicating if needed.
    pub fn save(&self, output_dir: &Path) -> Result<PathBuf> {
        let stem = self
            .source
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("document");

        let filename: OsString = format!("{}.md", stem).into();
        let dest = crate::sorter::unique_dest(output_dir, &filename);
        std::fs::write(&dest, &self.content)?;
        Ok(dest)
    }
}
