use std::path::PathBuf;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    // Workspace
    pub base_dir: PathBuf,

    // PDF classification thresholds
    pub vlm_text_threshold: usize,      // ≤ this → VLM (very short, best quality)
    pub long_pdf_threshold: usize,      // > this → long PDF (head+tail sampling)
    pub scanned_long_threshold: usize,  // scanned PDFs > this → head+tail only
    pub scan_char_threshold: usize,     // avg chars/page below this → classified as scanned
    pub scan_sample_pages: usize,       // how many evenly-spaced pages to sample

    // Long PDF page sampling
    pub long_head_pages: usize,
    pub long_tail_pages: usize,

    // VLM endpoint (OpenAI-compatible, e.g. vLLM)
    pub vlm_base_url: String,
    pub vlm_model: String,
    pub vlm_max_tokens: usize,
    pub vlm_image_dpi: usize,
    pub vlm_max_workers: usize,
    pub vlm_retry_attempts: usize,
    pub vlm_retry_backoff: f64,

    // Runtime
    pub python_bin: String,
    pub parsers_dir: PathBuf,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            base_dir: PathBuf::from("/home/nullkuhl/docs"),
            vlm_text_threshold: 10,
            long_pdf_threshold: 200,
            scanned_long_threshold: 20,
            scan_char_threshold: 50,
            scan_sample_pages: 5,
            long_head_pages: 10,
            long_tail_pages: 10,
            vlm_base_url: "http://127.0.0.1:8000/v1".to_string(),
            vlm_model: "Qwen/Qwen3.6-27B-FP8".to_string(),
            vlm_max_tokens: 8192,
            vlm_image_dpi: 200,
            vlm_max_workers: 4,
            vlm_retry_attempts: 3,
            vlm_retry_backoff: 2.0,
            python_bin: "python3".to_string(),
            parsers_dir: PathBuf::from("parsers"),
        }
    }
}

impl Config {
    pub fn input_dir(&self) -> PathBuf { self.base_dir.join("input") }
    pub fn output_dir(&self) -> PathBuf { self.base_dir.join("output") }
    pub fn sorted_dir(&self) -> PathBuf { self.base_dir.join("sorted") }
    pub fn temp_dir(&self) -> PathBuf { self.base_dir.join("temp") }

    pub fn ensure_dirs(&self) -> anyhow::Result<()> {
        for path in [
            self.input_dir(),
            self.output_dir(),
            self.temp_dir(),
            self.sorted_dir().join("office"),
            self.sorted_dir().join("images"),
            self.sorted_dir().join("pdfs").join("vlm_text"),
            self.sorted_dir().join("pdfs").join("short_text"),
            self.sorted_dir().join("pdfs").join("short_scanned"),
            self.sorted_dir().join("pdfs").join("long_text"),
            self.sorted_dir().join("pdfs").join("long_scanned"),
        ] {
            std::fs::create_dir_all(&path)?;
        }
        Ok(())
    }
}
