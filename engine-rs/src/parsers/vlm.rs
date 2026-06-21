use std::path::Path;
use std::sync::Arc;
use anyhow::Result;
use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use tokio::task::JoinSet;
use crate::config::Config;
use crate::parsers::ParseResult;

/// Full prompt for page 1: identify document type, visual elements, then full content.
const SYSTEM_PROMPT: &str = "\
You are an expert multilingual document analyst specializing in Arabic and English documents.

For this document page provide:
1. Document type (Certificate, Invoice, Contract, Report, Form, etc.)
2. For each visual element detected (stamp, signature, logo, watermark, QR code, seal, \
photograph, border, fingerprint, embossing, hologram, diagram):
   - Element type
   - Description
   - Issuer/name if applicable
   - Location on the page

3. ## Full Content
Extract ALL text verbatim, preserving:
- Arabic text in correct RTL reading order
- Tables formatted as Markdown pipe-tables
- Headings using ## and ###
- Lists with proper indentation";

/// Condensed prompt for pages 2+: content only, no type/element preamble.
const CONTENT_ONLY_PROMPT: &str = "\
Extract the full content of this page as Markdown:
- All text verbatim
- Arabic text in correct RTL reading order
- Tables as Markdown pipe-tables
- Headings with ## or ###
- List any visual elements (stamps, signatures, logos) briefly";

/// Entry point — wraps errors into a ParseResult rather than propagating.
pub async fn parse(path: &Path, cfg: &Config, sem: Arc<tokio::sync::Semaphore>) -> ParseResult {
    match parse_inner(path, cfg, sem).await {
        Ok(r) => r,
        Err(e) => ParseResult::error_result(path.to_path_buf(), "vlm", e.to_string()),
    }
}

async fn parse_inner(path: &Path, cfg: &Config, sem: Arc<tokio::sync::Semaphore>) -> Result<ParseResult> {
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_lowercase();

    let (pages_b64, page_count): (Vec<String>, u32) = if ext == "pdf" {
        render_pdf_pages(path, cfg)?
    } else {
        // Direct image file
        let data = std::fs::read(path)?;
        (vec![B64.encode(&data)], 1)
    };

    if pages_b64.is_empty() {
        anyhow::bail!("No pages rendered from {}", path.display());
    }

    let client = Arc::new(
        reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(120))
            .build()?,
    );
    let cfg_arc = Arc::new(cfg.clone());

    let mut join_set: JoinSet<(usize, Result<String>)> = JoinSet::new();

    for (idx, b64) in pages_b64.into_iter().enumerate() {
        let client = Arc::clone(&client);
        let cfg_arc = Arc::clone(&cfg_arc);
        let sem = Arc::clone(&sem);

        join_set.spawn(async move {
            let _permit = sem.acquire().await;
            let result = call_vlm_with_retry(&client, &*cfg_arc, idx, &b64).await;
            (idx, result)
        });
    }

    // Collect results preserving page order
    let mut page_results: Vec<Option<String>> = vec![None; page_count as usize];

    while let Some(res) = join_set.join_next().await {
        match res {
            Ok((idx, Ok(text))) => page_results[idx] = Some(text),
            Ok((idx, Err(e))) => {
                page_results[idx] = Some(format!(
                    "> ⚠ Page {} extraction failed: {}",
                    idx + 1,
                    e
                ));
            }
            Err(e) => eprintln!("task join error: {e}"),
        }
    }

    // Combine pages: page 1 verbatim, pages 2+ prefixed with separator
    let mut parts = Vec::new();
    for (idx, maybe_text) in page_results.into_iter().enumerate() {
        let text = maybe_text
            .unwrap_or_else(|| format!("> ⚠ Page {} extraction failed: no result", idx + 1));
        if idx == 0 {
            parts.push(text);
        } else {
            parts.push(format!("---\n\n## Page {}\n\n{}", idx + 1, text));
        }
    }

    let combined = parts.join("\n\n");

    // Rough table count: sequences of pipe-table lines separated by non-pipe lines
    let table_count = count_tables(&combined);

    let source_name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("document");

    let header = format!(
        "---\nsource: {}\nparser: vlm\nmodel: {}\npages: {}\n---\n\n",
        source_name, cfg.vlm_model, page_count
    );

    Ok(ParseResult {
        source: path.to_path_buf(),
        parser: "vlm".to_string(),
        content: format!("{}{}", header, combined),
        page_count: Some(page_count),
        extras: serde_json::json!({ "table_count": table_count }),
        error: None,
    })
}

/// Render all pages of a PDF to base64 PNG strings using pdfium (pure Rust, no subprocess).
fn render_pdf_pages(path: &Path, cfg: &Config) -> Result<(Vec<String>, u32)> {
    crate::pdf_render::render_pages(path, cfg.vlm_image_dpi, cfg.pdfium_path.as_deref())
}

async fn call_vlm_with_retry(
    client: &reqwest::Client,
    cfg: &Config,
    page_idx: usize,
    b64: &str,
) -> Result<String> {
    let mut last_err: Option<anyhow::Error> = None;

    for attempt in 0..cfg.vlm_retry_attempts {
        if attempt > 0 {
            // Exponential backoff: 2.0, 4.0, 8.0 ...
            let wait = cfg.vlm_retry_backoff * (2.0f64.powi(attempt as i32 - 1));
            tokio::time::sleep(std::time::Duration::from_secs_f64(wait)).await;
        }
        match call_vlm_once(client, cfg, page_idx, b64).await {
            Ok(text) => return Ok(text),
            Err(e) => last_err = Some(e),
        }
    }

    Err(last_err.unwrap())
}

async fn call_vlm_once(
    client: &reqwest::Client,
    cfg: &Config,
    page_idx: usize,
    b64: &str,
) -> Result<String> {
    let prompt = if page_idx == 0 {
        SYSTEM_PROMPT
    } else {
        CONTENT_ONLY_PROMPT
    };

    let image_url = format!("data:image/png;base64,{}", b64);

    let body = serde_json::json!({
        "model": cfg.vlm_model,
        "max_tokens": cfg.vlm_max_tokens,
        "chat_template_kwargs": { "enable_thinking": false },
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": { "url": image_url }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    });

    let url = format!("{}/chat/completions", cfg.vlm_base_url.trim_end_matches('/'));

    let resp = client
        .post(&url)
        .header("Authorization", "Bearer dummy")
        .header("Content-Type", "application/json")
        .json(&body)
        .send()
        .await?;

    if !resp.status().is_success() {
        let status = resp.status();
        let body_text = resp.text().await.unwrap_or_default();
        anyhow::bail!("VLM API {} {}", status, body_text);
    }

    let json: serde_json::Value = resp.json().await?;

    let msg = &json["choices"][0]["message"];
    let text = msg["content"].as_str()
        .or_else(|| msg["reasoning"].as_str())
        .unwrap_or("")
        .to_string();

    if text.is_empty() {
        anyhow::bail!("VLM returned empty content: {}", json);
    }

    Ok(text)
}

/// Count Markdown pipe-tables as groups of consecutive pipe-starting lines.
fn count_tables(text: &str) -> usize {
    let mut count = 0;
    let mut in_table = false;

    for line in text.lines() {
        let is_pipe = line.trim_start().starts_with('|');
        if is_pipe && !in_table {
            in_table = true;
            count += 1;
        } else if !is_pipe {
            in_table = false;
        }
    }
    count
}
