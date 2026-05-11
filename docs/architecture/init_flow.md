# Start- und Initialisierungsfluss – Setuphelfer

_Phase 4 – Strukturelle Systemvereinfachung_

**Referenz Namen/Pfade/systemd:** [NAMING_AND_SERVICES.md](NAMING_AND_SERVICES.md) (ab 1.4.0).

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

## 5. Service-Definitionen (Produktion ab 1.4.0)

| Service | Datei (Vorlage) | ExecStart (Kern) |
|---------|----------------|------------------|
| **setuphelfer-backend** | `setuphelfer-backend.service` | `scripts/start-backend.sh` – **Port 8000** |
| **setuphelfer** | `setuphelfer.service` | `scripts/start-browser-production.sh` – Web-UI (**vite preview**), kein zweites Backend |

**Hinweis:** Die Web-UI-Unit startet **nicht** `./start.sh` (Vite-Dev), um Schreibzugriffe auf `frontend/node_modules/.vite` unter `/opt` zu vermeiden.

**Aktiver Pfad:** `./scripts/install-backend-service.sh` / `install-system.sh` richten **`setuphelfer-backend`** (und bei Vollinstallation **`setuphelfer`**) ein. Legacy: `pi-installer-backend.service`.

---

## 6. Was nicht ohne Prüfung geändert werden darf

- Boot-Reihenfolge (systemd, postinst)
- Hardware-Erkennung (NVMe, HDMI, Freenove)
- Persistenzpfade (config, logs)
- systemd-Unit-Dateien
