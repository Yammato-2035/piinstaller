# Start- und Initialisierungsfluss – PI-Installer

_Phase 4 – Strukturelle Systemvereinfachung_

## 1. Ziel

Start- und Initialisierungslogik soll nachvollziehbar und konsistent sein.

---

## 2. Startreihenfolge (Backend)

### 1. Skript

| Skript | Zweck |
|--------|-------|
| `start-backend.sh` | Venv prüfen, Port prüfen, uvicorn starten |
| `start.sh` | Backend + Frontend (npm run dev) |
| `start-pi-installer.sh` | Wartet auf Backend, Dialog (Tauri/Browser/Frontend) |

### 2. Backend-Startup (app.py)

1. `@app.on_event("startup")` → `_startup_init()`
2. `init_debug()`
3. `run_start()`
4. `_load_or_init_config()` → config.json laden/initialisieren
5. `app.state.app_settings`, `app.state.device_id`
6. `init_remote_db()` (falls Remote feature)
7. `_get_control_center_module().ensure_display_telemetry_autostart()` (OLED)

### 3. Shutdown

- `@app.on_event("shutdown")` → `run_end()`, duration_ms

---

## 3. Initialisierungsabhängigkeiten

| Komponente | Abhängigkeit |
|------------|--------------|
| Config | Vor allen API-Handlern |
| Remote-DB | CONFIG_PATH.parent |
| Control-Center-Modul | Lazy; erst bei Bedarf |
| OLED-Autostart | Control-Center-Modul |

---

## 4. Kritische Bereiche – nicht ohne Prüfung ändern

| Bereich | Warum kritisch |
|---------|----------------|
| Reihenfolge init_debug → config → remote_db | Debug und Config müssen vor DB-Init laufen |
| OLED-Autostart | Hardware-nahe, systemd-Service |
| Port 8000 / PI_INSTALLER_BACKEND_PORT | Frontend, Tauri, Doku erwarten 8000 |

---

## 5. Service-Definitionen

| Service | Datei | ExecStart |
|---------|-------|-----------|
| pi-installer | pi-installer.service, debian/ | start.sh (Backend + Frontend) |
| pi-installer-backend | pi-installer-backend.service | start-backend.sh (nur Backend) |

**Aktiver Installationspfad:** `./scripts/install-backend-service.sh` richtet `pi-installer-backend` ein.

---

## 6. Was nicht ohne Prüfung geändert werden darf

- Boot-Reihenfolge (systemd, postinst)
- Hardware-Erkennung (NVMe, HDMI, Freenove)
- Persistenzpfade (config, logs)
- systemd-Unit-Dateien
