use std::path::Path;

use anyhow::Result;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileResult {
    pub source: String,
    pub parser: String,
    pub pages: Option<usize>,
    pub ok: bool,
    pub error: Option<String>,
    pub elapsed_s: Option<f64>,
    pub table_count: Option<usize>,
}

#[derive(Debug, Serialize)]
struct Summary<'a> {
    total_elapsed_s: f64,
    files: &'a [FileResult],
}

pub fn write_summary(output_dir: &Path, results: &[FileResult], elapsed_s: f64) -> Result<()> {
    let summary = Summary {
        total_elapsed_s: (elapsed_s * 100.0).round() / 100.0,
        files: results,
    };
    let json = serde_json::to_string_pretty(&summary)?;
    std::fs::write(output_dir.join("_summary.json"), json)?;
    Ok(())
}
