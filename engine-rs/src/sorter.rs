use std::collections::HashMap;
use std::ffi::OsString;
use std::path::{Path, PathBuf};
use anyhow::Result;
use walkdir::WalkDir;
use crate::config::Config;
use crate::detector::{classify, DocClass};

pub fn sort_input(cfg: &Config) -> Result<HashMap<DocClass, Vec<PathBuf>>> {
    let mut result: HashMap<DocClass, Vec<PathBuf>> = HashMap::new();

    let entries: Vec<_> = WalkDir::new(cfg.input_dir())
        .min_depth(1)
        .max_depth(1)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .collect();

    for entry in entries {
        let src = entry.path();
        let cls = classify(src, cfg);

        if let Some(subdir) = cls.sorted_subdir() {
            let dest_dir = cfg.sorted_dir().join(subdir);
            std::fs::create_dir_all(&dest_dir)?;
            let filename = src.file_name().unwrap_or_default();
            let dest = unique_dest(&dest_dir, filename);
            std::fs::rename(src, &dest)?;
            result.entry(cls).or_default().push(dest);
        }
    }

    Ok(result)
}

/// Return a path under `dir` that does not yet exist.
/// If `dir/filename` exists, tries `dir/stem_1.ext`, `dir/stem_2.ext`, ...
pub fn unique_dest(dir: &Path, filename: &std::ffi::OsStr) -> PathBuf {
    let candidate = dir.join(filename);
    if !candidate.exists() {
        return candidate;
    }

    let name = Path::new(filename);
    let stem = name.file_stem().and_then(|s| s.to_str()).unwrap_or("");
    let ext = name.extension().and_then(|e| e.to_str()).unwrap_or("");

    let mut n = 1usize;
    loop {
        let new_name: OsString = if ext.is_empty() {
            format!("{}_{}", stem, n).into()
        } else {
            format!("{}_{}.{}", stem, n, ext).into()
        };
        let c = dir.join(&new_name);
        if !c.exists() {
            return c;
        }
        n += 1;
    }
}
