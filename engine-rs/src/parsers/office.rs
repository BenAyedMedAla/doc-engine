use std::path::Path;
use anyhow::Result;
use crate::detector::{python_cmd, scripts_dir};
use crate::parsers::ParseResult;

/// Parse an office document via the Kreuzberg Python helper.
pub fn parse(path: &Path) -> ParseResult {
    match parse_inner(path) {
        Ok(r) => r,
        Err(e) => ParseResult::error_result(path.to_path_buf(), "kreuzberg", e.to_string()),
    }
}

fn parse_inner(path: &Path) -> Result<ParseResult> {
    let output = std::process::Command::new(python_cmd())
        .arg(scripts_dir().join("parse_office.py"))
        .arg(path)
        .output()?;

    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("parse_office.py failed: {err}");
    }

    let json: serde_json::Value = serde_json::from_slice(&output.stdout)
        .map_err(|e| anyhow::anyhow!("parse_office.py returned invalid JSON: {e}"))?;

    if let Some(err) = json.get("error").and_then(|e| e.as_str()) {
        if !err.is_empty() {
            anyhow::bail!("{err}");
        }
    }

    let content = json
        .get("content")
        .and_then(|c| c.as_str())
        .unwrap_or("")
        .to_string();

    let pages = json.get("pages").and_then(|p| p.as_u64()).map(|p| p as u32);

    Ok(ParseResult {
        source: path.to_path_buf(),
        parser: "kreuzberg".to_string(),
        content,
        page_count: pages,
        extras: json.get("extras").cloned().unwrap_or(serde_json::Value::Null),
        error: None,
    })
}
