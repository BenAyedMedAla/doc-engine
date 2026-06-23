mod config;
mod detector;
mod extractor;
mod pipeline;
mod sorter;
mod summary;

use std::path::PathBuf;
use std::time::Instant;

use anyhow::Result;
use clap::Parser;

use config::Config;

#[derive(Parser, Debug)]
#[command(
    name = "doc-engine",
    about = "Document ingestion & extraction pipeline (Rust orchestrator + Python parsers)"
)]
struct Args {
    /// Workspace root (contains input/, sorted/, output/, temp/)
    #[arg(long)]
    base_dir: Option<PathBuf>,

    /// Process a single file directly, bypassing sorting
    #[arg(long)]
    file: Option<PathBuf>,

    /// Skip sorting; process files already in sorted/
    #[arg(long)]
    no_sort: bool,

    /// Pages above this count → long PDF (head+tail sampling)
    #[arg(long)]
    long_threshold: Option<usize>,

    /// Pages to take from the start of a long PDF
    #[arg(long)]
    head: Option<usize>,

    /// Pages to take from the end of a long PDF
    #[arg(long)]
    tail: Option<usize>,

    /// Avg chars/page below this → scanned PDF
    #[arg(long)]
    scan_threshold: Option<usize>,

    /// OpenAI-compatible VLM endpoint base URL
    #[arg(long)]
    vlm_url: Option<String>,

    /// VLM model name
    #[arg(long)]
    vlm_model: Option<String>,

    /// Parallel page requests to VLM
    #[arg(long)]
    vlm_workers: Option<usize>,

    /// DPI for rendering PDF pages before VLM
    #[arg(long)]
    vlm_dpi: Option<usize>,

    /// Python interpreter to use for parser scripts
    #[arg(long)]
    python_bin: Option<String>,

    /// Directory containing the Python parser scripts
    #[arg(long)]
    parsers_dir: Option<PathBuf>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let mut cfg = Config::default();

    // Apply CLI overrides
    if let Some(d) = args.base_dir        { cfg.base_dir          = d; }
    if let Some(t) = args.long_threshold  { cfg.long_pdf_threshold = t; }
    if let Some(h) = args.head            { cfg.long_head_pages    = h; }
    if let Some(t) = args.tail            { cfg.long_tail_pages    = t; }
    if let Some(t) = args.scan_threshold  { cfg.scan_char_threshold = t; }
    if let Some(u) = args.vlm_url         { cfg.vlm_base_url       = u; }
    if let Some(m) = args.vlm_model       { cfg.vlm_model          = m; }
    if let Some(w) = args.vlm_workers     { cfg.vlm_max_workers    = w; }
    if let Some(d) = args.vlm_dpi         { cfg.vlm_image_dpi      = d; }
    if let Some(b) = args.python_bin      { cfg.python_bin         = b; }
    if let Some(d) = args.parsers_dir     { cfg.parsers_dir        = d; }

    println!("── Document Ingestion Pipeline ─────────────────────────────────");
    println!("   Workspace : {}", cfg.base_dir.display());
    println!("   VLM       : {}  ({})", cfg.vlm_base_url, cfg.vlm_model);
    println!(
        "   Long PDF  : > {} pages  → head {} + tail {}",
        cfg.long_pdf_threshold, cfg.long_head_pages, cfg.long_tail_pages
    );

    cfg.ensure_dirs()?;

    // Build the file list
    let files: Vec<(PathBuf, detector::DocClass)> = if let Some(single) = args.file {
        let path = single.canonicalize()?;
        let cls = detector::classify(&path, &cfg);
        println!(
            "\n  Single file: {}  [{}]",
            path.file_name().unwrap_or_default().to_string_lossy(),
            cls.label()
        );
        vec![(path, cls)]
    } else if args.no_sort {
        walkdir::WalkDir::new(cfg.sorted_dir())
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| {
                e.file_type().is_file()
                    && !e.file_name().to_string_lossy().starts_with('_')
            })
            .map(|e| {
                let p = e.into_path();
                let cls = detector::classify(&p, &cfg);
                (p, cls)
            })
            .collect()
    } else {
        println!("\n── Sorting input files ──────────────────────────────────");
        sorter::sort_input(&cfg)?
    };

    if files.is_empty() {
        println!("  [pipeline] no files to process");
        return Ok(());
    }

    println!("\n── Processing {} file(s) ─────────────────────────────────", files.len());
    let t0 = Instant::now();

    let results = pipeline::process_all(files, &cfg).await?;

    let elapsed = t0.elapsed().as_secs_f64();
    let ok_count  = results.iter().filter(|r| r.ok).count();
    let err_count = results.len() - ok_count;

    summary::write_summary(&cfg.output_dir(), &results, elapsed)?;

    let (mins, secs) = (elapsed as u64 / 60, elapsed % 60.0);
    let elapsed_str = if mins > 0 {
        format!("{}m {:.1}s", mins, secs)
    } else {
        format!("{:.1}s", secs)
    };

    println!(
        "\n── Done — {}/{} succeeded, {} errors  [total: {}]\n   Output:  {}\n   Summary: {}",
        ok_count,
        results.len(),
        err_count,
        elapsed_str,
        cfg.output_dir().display(),
        cfg.output_dir().join("_summary.json").display(),
    );

    Ok(())
}
