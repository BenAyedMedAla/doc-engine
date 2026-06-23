/// Sort every file in input/ into its appropriate sorted/ subfolder.
///
/// Classification runs in parallel via rayon — all files are classified
/// concurrently (O(1) PDF XRef reads + lightweight text sampling), then
/// moved sequentially (filesystem renames don't benefit from parallelism
/// on a single drive).
use std::fs;
use std::path::{Path, PathBuf};

use anyhow::Result;
use rayon::prelude::*;

use crate::config::Config;
use crate::detector::{classify, DocClass};

fn unique_dest(dest: &Path) -> PathBuf {
    if !dest.exists() {
        return dest.to_path_buf();
    }
    let stem = dest.file_stem().unwrap_or_default().to_string_lossy();
    let ext = dest
        .extension()
        .map(|e| format!(".{}", e.to_string_lossy()))
        .unwrap_or_default();
    let parent = dest.parent().unwrap_or(Path::new("."));
    (1..)
        .map(|i| parent.join(format!("{}_{}{}", stem, i, ext)))
        .find(|p| !p.exists())
        .unwrap()
}

/// Classify and move every file from input/ to its sorted/ subfolder.
/// Returns a vec of (sorted_path, DocClass) pairs for downstream use.
pub fn sort_input(cfg: &Config) -> Result<Vec<(PathBuf, DocClass)>> {
    cfg.ensure_dirs()?;

    let mut files: Vec<PathBuf> = fs::read_dir(cfg.input_dir())?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.is_file())
        .collect();
    files.sort();

    if files.is_empty() {
        println!("  [sorter] input/ is empty — nothing to sort");
        return Ok(vec![]);
    }

    // Classify all files in parallel (rayon thread pool, no GIL)
    let classified: Vec<(PathBuf, DocClass)> = files
        .par_iter()
        .map(|src| (src.clone(), classify(src, cfg)))
        .collect();

    // Move files sequentially after classification
    let mut result = Vec::new();
    for (src, cls) in classified {
        if cls == DocClass::Unknown {
            println!(
                "  [skip]   {}  (unrecognised extension)",
                src.file_name().unwrap_or_default().to_string_lossy()
            );
            continue;
        }

        let subdir = cls.subdir().unwrap();
        let dest_dir = cfg.sorted_dir().join(subdir);
        let dest = unique_dest(&dest_dir.join(src.file_name().unwrap()));

        fs::rename(&src, &dest)?;
        println!(
            "  [{:18}]  {}",
            cls.label(),
            src.file_name().unwrap_or_default().to_string_lossy()
        );
        result.push((dest, cls));
    }

    Ok(result)
}
