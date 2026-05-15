//! Read-only Workspace-Scan für Development Dashboard (Standalone ohne Backend).

use std::path::{Path, PathBuf};
use std::process::Command;

use serde::Serialize;
use serde_json::{json, Value};

#[derive(Serialize)]
struct ScanResult {
    workspace_root: String,
    warnings: Vec<String>,
    version: Option<Value>,
    frontend_package: Option<Value>,
    git: Value,
    evidence_files: Value,
    matrix: Value,
    modules: Vec<Value>,
}

fn resolve_workspace_root(workspace_root: Option<String>) -> Result<PathBuf, String> {
    if let Some(raw) = workspace_root {
        let p = PathBuf::from(raw.trim());
        if p.is_absolute() && p.join("config/version.json").is_file() {
            return Ok(p);
        }
        return Err(format!("Ungültiger workspace_root: {}", p.display()));
    }
    if let Ok(env) = std::env::var("SETUPHELFER_DEV_WORKSPACE_ROOT") {
        let p = PathBuf::from(env.trim());
        if p.join("config/version.json").is_file() {
            return Ok(p);
        }
    }
    let mut cur = std::env::current_dir().map_err(|e| e.to_string())?;
    for _ in 0..8 {
        if cur.join("config/version.json").is_file() {
            return Ok(cur);
        }
        if !cur.pop() {
            break;
        }
    }
    Err("Workspace-Root nicht gefunden (config/version.json)".to_string())
}

fn read_json_file(path: &Path) -> Option<Value> {
    let raw = std::fs::read_to_string(path).ok()?;
    serde_json::from_str(&raw).ok()
}

fn git_output(repo: &Path, args: &[&str]) -> Option<String> {
    let out = Command::new("git")
        .arg("-C")
        .arg(repo)
        .args(args)
        .output()
        .ok()?;
    if !out.status.success() {
        return None;
    }
    let s = String::from_utf8_lossy(&out.stdout).trim().to_string();
    if s.is_empty() {
        None
    } else {
        Some(s)
    }
}

fn scan_git(repo: &Path) -> Value {
    let mut git = json!({
        "git_head": null,
        "git_branch": null,
        "git_dirty_count": null,
        "git_recent": [],
    });
    if let Some(h) = git_output(repo, &["rev-parse", "HEAD"]) {
        git["git_head"] = json!(h.chars().take(64).collect::<String>());
    }
    if let Some(b) = git_output(repo, &["rev-parse", "--abbrev-ref", "HEAD"]) {
        if b != "HEAD" {
            git["git_branch"] = json!(b);
        }
    }
    if let Ok(out) = Command::new("git")
        .arg("-C")
        .arg(repo)
        .args(["status", "--porcelain"])
        .output()
    {
        if out.status.success() {
            let stdout = String::from_utf8_lossy(&out.stdout);
            let dirty_count = stdout
                .lines()
                .filter(|l| !l.trim().is_empty())
                .count();
            git["git_dirty_count"] = json!(dirty_count);
        }
    }
    if let Ok(out) = Command::new("git")
        .arg("-C")
        .arg(repo)
        .args(["log", "--oneline", "-5"])
        .output()
    {
        if out.status.success() {
            let recent: Vec<String> = String::from_utf8_lossy(&out.stdout)
                .lines()
                .map(|s| s.to_string())
                .collect();
            git["git_recent"] = json!(recent);
        }
    }
    git
}

fn scan_evidence(repo: &Path) -> Value {
    let gates_dir = repo.join("docs/evidence/release-gates");
    let names = [
        "test_inventory.json",
        "current_failures.json",
        "release_readiness_gate.json",
        "backup_restore_release_gate.json",
    ];
    let mut files = serde_json::Map::new();
    for name in names {
        let p = gates_dir.join(name);
        let mut entry = json!({
            "path": format!("docs/evidence/release-gates/{}", name),
            "exists": p.is_file(),
        });
        if let Some(data) = read_json_file(&p) {
            entry["data"] = data;
            entry["status"] = json!("ok");
        } else if p.is_file() {
            entry["status"] = json!("unreadable");
        } else {
            entry["status"] = json!("missing");
        }
        files.insert(name.to_string(), entry);
    }
    Value::Object(files)
}

fn scan_modules(repo: &Path) -> Vec<Value> {
    let dir = repo.join("docs/dev-dashboard/modules");
    let Ok(entries) = std::fs::read_dir(&dir) else {
        return vec![];
    };
    let mut out = Vec::new();
    for ent in entries.flatten() {
        let path = ent.path();
        if path.extension().and_then(|s| s.to_str()) != Some("json") {
            continue;
        }
        if let Some(data) = read_json_file(&path) {
            if let Some(obj) = data.as_object() {
                let mut m = obj.clone();
                if let Ok(rel) = path.strip_prefix(repo) {
                    m.insert(
                        "source".to_string(),
                        json!(rel.to_string_lossy().replace('\\', "/")),
                    );
                }
                out.push(Value::Object(m));
            }
        }
    }
    out.sort_by(|a, b| {
        a.get("title")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .cmp(b.get("title").and_then(|v| v.as_str()).unwrap_or(""))
    });
    out
}

#[tauri::command]
pub fn get_dev_dashboard_workspace_status(
    workspace_root: Option<String>,
) -> Result<Value, String> {
    let repo = resolve_workspace_root(workspace_root)?;
    let mut warnings = Vec::new();

    let version_path = repo.join("config/version.json");
    let version = read_json_file(&version_path);
    if version.is_none() {
        warnings.push("workspace_version_unreadable".to_string());
    }

    let fe_pkg_path = repo.join("frontend/package.json");
    let frontend_package = read_json_file(&fe_pkg_path);

    let matrix_path = repo.join("docs/roadmap/STATUS_MATRIX.md");
    let matrix_text = matrix_path.is_file().then(|| std::fs::read_to_string(&matrix_path).ok()).flatten();
    let matrix = json!({
        "path": "docs/roadmap/STATUS_MATRIX.md",
        "exists": matrix_path.is_file(),
        "lines": matrix_text.as_ref().map(|t| t.lines().count()),
        "text": matrix_text,
    });

    let scan = ScanResult {
        workspace_root: repo.to_string_lossy().to_string(),
        warnings,
        version,
        frontend_package,
        git: scan_git(&repo),
        evidence_files: scan_evidence(&repo),
        matrix,
        modules: scan_modules(&repo),
    };

    serde_json::to_value(scan).map_err(|e| e.to_string())
}
