use std::path::PathBuf;
use std::process::Command;
use std::thread;
use std::time::Duration;

use tauri::{Manager, WebviewUrl};
use tauri::webview::WebviewWindowBuilder;

mod dev_dashboard_standalone;

#[tauri::command]
async fn open_development_cockpit(app: tauri::AppHandle) -> Result<String, String> {
    const LABEL: &str = "cockpit";
    if let Some(win) = app.get_webview_window(LABEL) {
        let _ = win.unminimize();
        let _ = win.show();
        let _ = win.set_focus();
        return Ok("focused".into());
    }
    let url = if cfg!(debug_assertions) {
        WebviewUrl::External(
            "http://localhost:5173/?window=cockpit"
                .parse::<url::Url>()
                .map_err(|e: url::ParseError| e.to_string())?,
        )
    } else {
        WebviewUrl::App("index.html?window=cockpit".into())
    };
    WebviewWindowBuilder::new(&app, LABEL, url)
        .title("SetupHelfer — Development Control Center")
        .inner_size(1440.0, 900.0)
        .min_inner_size(960.0, 600.0)
        .build()
        .map_err(|e| e.to_string())?;
    Ok("opened".into())
}

#[tauri::command]
fn exit_app() {
    std::process::exit(0);
}

#[tauri::command]
fn launch_update_terminal() -> Result<String, String> {
    let shell_cmd = "sudo apt update && sudo apt upgrade; echo ''; read -p 'Druecke Enter zum Schliessen' dummy";
    let terms: [(&str, &[&str]); 8] = [
        ("gnome-terminal", &["--", "bash", "-lc"]),
        ("xfce4-terminal", &["-e"]),
        ("konsole", &["-e", "bash", "-lc"]),
        ("mate-terminal", &["--", "bash", "-lc"]),
        ("xterm", &["-e"]),
        ("lxterminal", &["-e"]),
        ("kitty", &["bash", "-lc"]),
        ("alacritty", &["-e", "bash", "-lc"]),
    ];

    for (term, prefix) in terms {
        let mut cmd = Command::new(term);
        if term == "xfce4-terminal" || term == "xterm" || term == "lxterminal" {
            let wrapped = format!("bash -lc \"{}\"", shell_cmd.replace('"', "\\\""));
            for p in prefix {
                cmd.arg(p);
            }
            cmd.arg(wrapped);
        } else {
            for p in prefix {
                cmd.arg(p);
            }
            cmd.arg(shell_cmd);
        }
        if cmd.spawn().is_ok() {
            return Ok(format!("Terminal geoeffnet ({term})."));
        }
    }
    Err("Kein passendes Terminalprogramm gefunden.".to_string())
}

/// Gibt den empfohlenen Ordner für Dokumentations-Screenshots zurück.
#[tauri::command]
async fn get_screenshots_output_dir(app: tauri::AppHandle) -> Result<String, String> {
    let doc = app.path().document_dir()
        .map_err(|e: tauri::Error| e.to_string())?;
    let dir = doc.join("SetupHelfer").join("docs").join("screenshots");
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
        .invoke_handler(tauri::generate_handler![
            exit_app,
            get_screenshots_output_dir,
            copy_screenshot_to,
            launch_update_terminal,
            dev_dashboard_standalone::get_dev_dashboard_workspace_status,
            open_development_cockpit
        ])
        .setup(|app| {
            let handle = app.handle().clone();
            thread::spawn(move || {
                // Kurz warten, damit der erste WebView-Frame gerendert wird, bevor das Fenster sichtbar wird.
                // Behebt unter Linux (Wayland/X11) das „Grafik in Linien zerteilte“-Problem beim Start.
                thread::sleep(Duration::from_millis(280));
                let app_handle = handle.clone();
                let _ = handle.run_on_main_thread(move || {
                    if let Some(win) = app_handle.get_webview_window("main") {
                        let _ = win.set_size(tauri::LogicalSize::new(1280.0, 800.0));
                        let _ = win.show();
                        let _ = win.set_focus();
                        // Repaint erzwingen (hilft bei Compositor-Bugs: Bild richtet sich erst beim Bewegen aus).
                        let win2 = win.clone();
                        let _ = win.run_on_main_thread(move || {
                            let _ = win2.set_size(tauri::LogicalSize::new(1281.0, 800.0));
                            let _ = win2.set_size(tauri::LogicalSize::new(1280.0, 800.0));
                        });
                    }
                });
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
