mod config;
mod detector;
mod parsers;
mod pdf_render;
mod pipeline;
mod sorter;

use std::path::PathBuf;
use clap::Parser;
use config::Config;

#[derive(Parser, Debug)]
#[command(name = "engine-rs", about = "Document ingestion & extraction engine (Rust)")]
struct Cli {
    /// Process a single file and exit (bypasses sorting)
    #[arg(long)]
    file: Option<PathBuf>,

    /// Skip the sorting step and process sorted/ directly
    #[arg(long)]
    no_sort: bool,

    /// Workspace base directory
    #[arg(long)]
    base_dir: Option<PathBuf>,

    /// Pages threshold above which a text PDF is routed to head+tail extraction
    #[arg(long)]
    long_threshold: Option<u32>,

    /// Head pages to extract from long PDFs
    #[arg(long)]
    head: Option<u32>,

    /// Tail pages to extract from long PDFs
    #[arg(long)]
    tail: Option<u32>,

    /// Avg chars/page threshold below which a PDF is classified as scanned
    #[arg(long)]
    scan_threshold: Option<u32>,

    /// VLM endpoint base URL (OpenAI-compatible)
    #[arg(long)]
    vlm_url: Option<String>,

    /// VLM model name
    #[arg(long)]
    vlm_model: Option<String>,

    /// Number of parallel VLM page requests
    #[arg(long)]
    vlm_workers: Option<usize>,

    /// DPI used when rendering PDF pages to images
    #[arg(long)]
    vlm_dpi: Option<u32>,

    /// Path to libpdfium.so (auto-detected from PDFIUM_PATH env / active venv if not set)
    #[arg(long)]
    pdfium_path: Option<String>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    let mut cfg = Config::default();

    if let Some(d) = cli.base_dir {
        cfg.base_dir = d;
    }
    if let Some(t) = cli.long_threshold {
        cfg.long_pdf_threshold = t;
    }
    if let Some(h) = cli.head {
        cfg.long_head_pages = h;
    }
    if let Some(t) = cli.tail {
        cfg.long_tail_pages = t;
    }
    if let Some(t) = cli.scan_threshold {
        cfg.scan_char_threshold = t;
    }
    if let Some(url) = cli.vlm_url {
        cfg.vlm_base_url = url;
    }
    if let Some(model) = cli.vlm_model {
        cfg.vlm_model = model;
    }
    if let Some(w) = cli.vlm_workers {
        cfg.vlm_max_workers = w;
    }
    if let Some(dpi) = cli.vlm_dpi {
        cfg.vlm_image_dpi = dpi;
    }
    if let Some(p) = cli.pdfium_path {
        cfg.pdfium_path = Some(p);
    }

    if let Some(file_path) = cli.file {
        // Single-file mode: classify → process → save
        cfg.ensure_dirs()?;
        let cls = detector::classify(&file_path, &cfg);
        println!("Classified as: {}", cls.as_str());

        let sem = std::sync::Arc::new(tokio::sync::Semaphore::new(cfg.vlm_max_workers));
        let result = pipeline::process_file(&file_path, cls, &cfg, sem).await;
        if result.ok() {
            let out = result.save(&cfg.output_dir())?;
            println!("Saved: {}", out.display());
        } else {
            eprintln!(
                "Error: {}",
                result.error.as_deref().unwrap_or("unknown error")
            );
            std::process::exit(1);
        }
    } else {
        pipeline::run(&cfg, !cli.no_sort, None).await?;
    }

    Ok(())
}
