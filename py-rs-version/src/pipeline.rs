/// Main pipeline orchestrator.
///
/// Each file is dispatched as an independent tokio task.  Concurrency per
/// parser type is capped by semaphores:
///   - Office (Kreuzberg, CPU-only)  → 8 concurrent
///   - Docling (GPU layout+tables)   → 2 concurrent  (VRAM-bound)
///   - VLM (network to vLLM server)  → 4 concurrent  (server-side limit)
///
/// Long PDFs (>threshold pages) have their head+tail pages extracted to a
/// temp file by the Rust extractor before the Python parser is called.
/// The temp file is deleted after the parser returns.
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::Instant;

use anyhow::Result;
use tokio::process::Command;
use tokio::sync::Semaphore;

use crate::config::Config;
use crate::detector::DocClass;
use crate::extractor::extract_pdf_pages;
use crate::summary::FileResult;

const OFFICE_SLOTS: usize  = 8;
const DOCLING_SLOTS: usize = 1; // GPU-bound: one at a time prevents VRAM exhaustion
const VLM_SLOTS: usize     = 4;

// ── Python subprocess ─────────────────────────────────────────────────────────

async fn spawn_parser(
    python_bin: &str,
    script: &Path,
    input: &Path,
    output_dir: &Path,
    extra: &[(&str, String)],
) -> Result<(bool, serde_json::Value)> {
    let mut cmd = Command::new(python_bin);
    cmd.arg(script)
       .arg("--input").arg(input)
       .arg("--output-dir").arg(output_dir);
    for (flag, val) in extra {
        cmd.arg(flag).arg(val);
    }

    let out = cmd.output().await?;

    // Print parser stderr (progress / warnings) to our stdout
    if !out.stderr.is_empty() {
        eprint!("{}", String::from_utf8_lossy(&out.stderr));
    }

    // Last JSON line on stdout is the structured result
    let stdout = String::from_utf8_lossy(&out.stdout);
    let json_val: serde_json::Value = stdout
        .lines()
        .rev()
        .find(|l| l.trim_start().starts_with('{'))
        .and_then(|l| serde_json::from_str(l).ok())
        .unwrap_or(serde_json::Value::Null);

    Ok((out.status.success(), json_val))
}

fn make_file_result(
    source_name: &str,
    success: bool,
    json: serde_json::Value,
    elapsed_s: f64,
    stderr_err: Option<String>,
) -> FileResult {
    if !success || json.is_null() {
        return FileResult {
            source: source_name.to_string(),
            parser: json.get("parser").and_then(|v| v.as_str()).unwrap_or("error").to_string(),
            pages: None,
            ok: false,
            error: stderr_err.or_else(|| Some("parser process failed or returned no JSON".to_string())),
            elapsed_s: Some(elapsed_s),
            table_count: None,
        };
    }

    FileResult {
        source:      source_name.to_string(),
        parser:      json["parser"].as_str().unwrap_or("").to_string(),
        pages:       json["pages"].as_u64().map(|p| p as usize),
        ok:          json["ok"].as_bool().unwrap_or(false),
        error:       json["error"].as_str().filter(|s| !s.is_empty()).map(String::from),
        elapsed_s:   Some(elapsed_s),
        table_count: json["table_count"].as_u64().map(|t| t as usize),
    }
}

// ── Per-file task ─────────────────────────────────────────────────────────────

async fn process_one(path: PathBuf, cls: DocClass, cfg: Arc<Config>, sem: Arc<Semaphore>) -> FileResult {
    let _permit = sem.acquire().await.unwrap();
    let t0 = Instant::now();

    let source_name = path
        .file_name()
        .unwrap_or_default()
        .to_string_lossy()
        .to_string();

    // Long PDF: extract head+tail pages to a temp file first
    let (parse_path, is_temp) = match cls {
        DocClass::PdfLongText | DocClass::PdfLongScan => {
            let tmp = cfg.temp_dir().join(format!("_sample_{}", source_name));
            match extract_pdf_pages(&path, &tmp, cfg.long_head_pages, cfg.long_tail_pages) {
                Ok(n) => {
                    println!(
                        "    [pipeline] {} — extracted {} pages (head {} + tail {}) → {}",
                        source_name, n, cfg.long_head_pages, cfg.long_tail_pages,
                        tmp.file_name().unwrap_or_default().to_string_lossy()
                    );
                    (tmp, true)
                }
                Err(e) => {
                    eprintln!("    [pipeline] page extraction failed for {}: {}", source_name, e);
                    (path.clone(), false)
                }
            }
        }
        _ => (path.clone(), false),
    };

    let script = cfg.parsers_dir.join(cls.parser_script());

    // VLM args passed only to vlm_parser.py
    let vlm_extra: Vec<(&str, String)> = vec![
        ("--vlm-url",      cfg.vlm_base_url.clone()),
        ("--vlm-model",    cfg.vlm_model.clone()),
        ("--vlm-tokens",   cfg.vlm_max_tokens.to_string()),
        ("--vlm-dpi",      cfg.vlm_image_dpi.to_string()),
        ("--vlm-workers",  cfg.vlm_max_workers.to_string()),
        ("--vlm-retries",  cfg.vlm_retry_attempts.to_string()),
        ("--vlm-backoff",  cfg.vlm_retry_backoff.to_string()),
    ];

    let extra: &[(&str, String)] = match cls {
        DocClass::Office | DocClass::PdfShortText => &[],
        _ => &vlm_extra,
    };

    let (success, json) =
        spawn_parser(&cfg.python_bin, &script, &parse_path, &cfg.output_dir(), extra)
            .await
            .unwrap_or_else(|e| (false, serde_json::Value::String(e.to_string())));

    let elapsed = t0.elapsed().as_secs_f64();

    // Clean up temp file
    if is_temp {
        let _ = std::fs::remove_file(&parse_path);
    }

    let mut result = make_file_result(&source_name, success, json, elapsed, None);
    // Always use original filename in the result (not the temp name)
    result.source = source_name.clone();

    if result.ok {
        println!("    ✓  {}  ({:.1}s)", source_name, elapsed);
    } else {
        println!(
            "    ✗  {}  ERROR: {}",
            source_name,
            result.error.as_deref().unwrap_or("unknown")
        );
    }

    result
}

// ── Public entry point ────────────────────────────────────────────────────────

pub async fn process_all(files: Vec<(PathBuf, DocClass)>, cfg: &Config) -> Result<Vec<FileResult>> {
    let cfg = Arc::new(cfg.clone());

    let office_sem  = Arc::new(Semaphore::new(OFFICE_SLOTS));
    let docling_sem = Arc::new(Semaphore::new(DOCLING_SLOTS));
    let vlm_sem     = Arc::new(Semaphore::new(VLM_SLOTS));

    let mut handles = Vec::with_capacity(files.len());

    for (path, cls) in files {
        let cfg_ref = Arc::clone(&cfg);
        let sem = match cls {
            DocClass::Office       => Arc::clone(&office_sem),
            DocClass::PdfShortText => Arc::clone(&docling_sem),
            _                      => Arc::clone(&vlm_sem),
        };

        handles.push(tokio::spawn(process_one(path, cls, cfg_ref, sem)));
    }

    let mut results = Vec::with_capacity(handles.len());
    for handle in handles {
        results.push(handle.await?);
    }
    Ok(results)
}
