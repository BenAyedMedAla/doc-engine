use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct Config {
    pub base_dir: PathBuf,

    // PDF classification thresholds
    pub vlm_text_threshold: u32,
    pub long_pdf_threshold: u32,
    pub scanned_long_threshold: u32,
    pub scan_char_threshold: u32,
    pub scan_sample_pages: usize,

    // Long PDF sampling
    pub long_head_pages: u32,
    pub long_tail_pages: u32,

    // Path to libpdfium.so (overrides PDFIUM_PATH env / auto-discovery)
    pub pdfium_path: Option<String>,

    // VLM endpoint (OpenAI-compatible)
    pub vlm_base_url: String,
    pub vlm_model: String,
    pub vlm_max_tokens: u32,
    pub vlm_image_dpi: u32,
    pub vlm_max_workers: usize,
    pub vlm_retry_attempts: u32,
    pub vlm_retry_backoff: f64,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            base_dir: PathBuf::from("/home/nullkuhl/docs"),
            pdfium_path: None,
            vlm_text_threshold: 10,
            long_pdf_threshold: 200,
            scanned_long_threshold: 20,
            scan_char_threshold: 50,
            scan_sample_pages: 5,
            long_head_pages: 10,
            long_tail_pages: 10,
            vlm_base_url: "http://197.46.212.11:8000/v1".to_string(),
            vlm_model: "Qwen/Qwen3.6-27B-FP8".to_string(),
            vlm_max_tokens: 8192,
            vlm_image_dpi: 200,
            vlm_max_workers: 4,
            vlm_retry_attempts: 3,
            vlm_retry_backoff: 2.0,
        }
    }
}

impl Config {
    pub fn input_dir(&self) -> PathBuf {
        self.base_dir.join("input")
    }

    pub fn output_dir(&self) -> PathBuf {
        self.base_dir.join("output")
    }

    pub fn sorted_dir(&self) -> PathBuf {
        self.base_dir.join("sorted")
    }

    pub fn temp_dir(&self) -> PathBuf {
        self.base_dir.join("temp")
    }

    pub fn ensure_dirs(&self) -> anyhow::Result<()> {
        for dir in [
            self.input_dir(),
            self.output_dir(),
            self.sorted_dir(),
            self.temp_dir(),
            self.sorted_dir().join("office"),
            self.sorted_dir().join("images"),
            self.sorted_dir().join("pdfs").join("vlm_text"),
            self.sorted_dir().join("pdfs").join("short_text"),
            self.sorted_dir().join("pdfs").join("short_scanned"),
            self.sorted_dir().join("pdfs").join("long_text"),
            self.sorted_dir().join("pdfs").join("long_scanned"),
        ] {
            std::fs::create_dir_all(&dir)?;
        }
        Ok(())
    }
}
