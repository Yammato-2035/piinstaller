use std::path::PathBuf;

use tauri::Manager;

#[tauri::command]
fn exit_app() {
    std::process::exit(0);
}

/// Gibt den empfohlenen Ordner für Dokumentations-Screenshots zurück.
#[tauri::command]
async fn get_screenshots_output_dir(app: tauri::AppHandle) -> Result<String, String> {
    let doc = app.path().document_dir()
        .map_err(|e: tauri::Error| e.to_string())?;
    let dir = doc.join("PI-Installer").join("docs").join("screenshots");
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.to_string_lossy().to_string())
}

/// Kopiert eine Screenshot-Datei an den Zielpfad (für Dokumentations-Screenshots).
#[tauri::command]
async fn copy_screenshot_to(source: String, target: String) -> Result<String, String> {
    let src = PathBuf::from(&source);
    let dst = PathBuf::from(&target);
    if !src.exists() {
        return Err(format!("Quelldatei nicht gefunden: {}", source));
    }
    if let Some(p) = dst.parent() {
        let _ = std::fs::create_dir_all(p);
    }
    std::fs::copy(&src, &dst).map_err(|e| format!("Kopieren fehlgeschlagen: {}", e))?;
    Ok(target)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_screenshots::init())
        .invoke_handler(tauri::generate_handler![exit_app, get_screenshots_output_dir, copy_screenshot_to])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
