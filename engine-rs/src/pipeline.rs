use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::Instant;
use anyhow::Result;
use tokio::sync::Semaphore;
use tokio::task::JoinSet;
use walkdir::WalkDir;
use crate::config::Config;
use crate::detector::{classify, extract_pdf_pages, DocClass};
use crate::parsers::{docling, office, vlm, ParseResult};
use crate::sorter::sort_input;

/// Run the full pipeline: optionally sort input, then process all sorted files.
pub async fn run(
    cfg: &Config,
    sort_first: bool,
    input_paths: Option<Vec<PathBuf>>,
) -> Result<Vec<ParseResult>> {
    cfg.ensure_dirs()?;

    if sort_first {
        println!("Sorting input files...");
        let sorted = sort_input(cfg)?;
        let total: usize = sorted.values().map(|v| v.len()).sum();
        println!("  Sorted {} files", total);
    }

    // Collect files to process
    let files: Vec<PathBuf> = if let Some(paths) = input_paths {
        paths
    } else {
        WalkDir::new(cfg.sorted_dir())
            .min_depth(2)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .map(|e| e.path().to_path_buf())
            .collect()
    };

    println!("Processing {} files...", files.len());
    let pipeline_start = Instant::now();

    // Global semaphore — caps total concurrent VLM vision requests to protect GPU memory.
    let vlm_sem = Arc::new(Semaphore::new(cfg.vlm_max_workers));

    let mut join_set: JoinSet<(ParseResult, f64, String)> = JoinSet::new();

    for path in files {
        let cfg = cfg.clone();
        let sem = Arc::clone(&vlm_sem);
        let cls = classify(&path, &cfg);
        let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("?").to_string();
        println!("  [{}] {}", cls.as_str(), name);

        join_set.spawn(async move {
            let t = Instant::now();
            let result = process_file(&path, cls, &cfg, sem).await;
            (result, t.elapsed().as_secs_f64(), name)
        });
    }

    let mut results = Vec::new();

    while let Some(join_result) = join_set.join_next().await {
        let (result, elapsed, name) = join_result?;
        if result.ok() {
            println!("    ok  {:.1}s  {}", elapsed, name);
            result.save(&cfg.output_dir()).ok();
        } else {
            println!(
                "    err {:.1}s  {}  — {}",
                elapsed,
                name,
                result.error.as_deref().unwrap_or("unknown")
            );
        }
        results.push(result);
    }

    let total_elapsed = pipeline_start.elapsed().as_secs_f64();
    write_summary(&cfg.output_dir(), &results, total_elapsed)?;

    let ok_count = results.iter().filter(|r| r.ok()).count();
    println!(
        "\nDone: {}/{} succeeded in {:.1}s",
        ok_count,
        results.len(),
        total_elapsed
    );

    Ok(results)
}

/// Process a single file: classify, route to the right parser.
/// Public so main.rs can call it for --file mode.
pub async fn process_file(path: &Path, cls: DocClass, cfg: &Config, vlm_sem: Arc<Semaphore>) -> ParseResult {
    match cls {
        DocClass::Office => office::parse(path),

        DocClass::Image | DocClass::PdfVlmText | DocClass::PdfShortScan => {
            vlm::parse(path, cfg, vlm_sem).await
        }

        DocClass::PdfShortText => docling::parse(path),

        DocClass::PdfLongText | DocClass::PdfLongScan => {
            let stem = path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("doc");
            let temp_path = cfg.temp_dir().join(format!("{}_excerpt.pdf", stem));

            match extract_pdf_pages(
                path,
                &temp_path,
                cfg.long_head_pages,
                cfg.long_tail_pages,
            ) {
                Err(e) => ParseResult::error_result(
                    path.to_path_buf(),
                    "vlm",
                    format!("page extraction failed: {e}"),
                ),
                Ok(_) => {
                    let mut result = vlm::parse(&temp_path, cfg, vlm_sem).await;
                    result.source = path.to_path_buf();
                    let _ = std::fs::remove_file(&temp_path);
                    result
                }
            }
        }

        DocClass::Unknown => ParseResult::error_result(
            path.to_path_buf(),
            "none",
            "unknown document type".to_string(),
        ),
    }
}

fn write_summary(output_dir: &Path, results: &[ParseResult], total_elapsed: f64) -> Result<()> {
    let files: Vec<serde_json::Value> = results
        .iter()
        .map(|r| {
            serde_json::json!({
                "source": r.source.file_name().and_then(|n| n.to_str()).unwrap_or(""),
                "parser": r.parser,
                "pages": r.page_count,
                "ok": r.ok(),
                "error": r.error,
                "elapsed_s": null,
                "table_count": r.extras.get("table_count").and_then(|v| v.as_u64()).unwrap_or(0),
            })
        })
        .collect();

    let summary = serde_json::json!({
        "total_elapsed_s": total_elapsed,
        "files": files,
    });

    let path = output_dir.join("_summary.json");
    std::fs::write(path, serde_json::to_string_pretty(&summary)?)?;
    Ok(())
}
