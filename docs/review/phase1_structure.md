# Phase 1 – Struktur stabilisieren

_Projektanalyse: Modulverantwortlichkeiten, Hauptpfade, Konfiguration, Debug, Initialisierung_

**Stand Pfade/Services (ab 1.4.0):** siehe **`docs/architecture/NAMING_AND_SERVICES.md`**. Tabellen unten nennen wo nötig **Legacy**-Pfade für Altinstallationen.

---

## 1. Modulübersicht

### Backend-Module (`backend/modules/`)

| Modul | Datei | Verantwortung |
|-------|-------|----------------|
| Backup | backup.py | Backup-Erstellung, Cloud-Integration, Klonen |
| Control Center | control_center.py | WLAN, SSH, VNC, Display, Performance, Lüfter, RGB, Drucker, Scanner |
| Dev-Umgebung | devenv.py | Entwicklungstools (Python, Node, Datenbanken, IDEs) |
| Mail | mail.py | Mailserver-Konfiguration |
| Raspberry Pi Config | raspberry_pi_config.py | config.txt, Overclocking, EDID, Overlays, UART |
| Security | security.py | Firewall (UFW), Fail2Ban, SSH-Härtung, Auto-Updates |
| Users | users.py | Benutzerverwaltung, Sudo-Passwort-Session |
| Webserver | webserver.py | Nginx/Apache-Konfiguration |
| Utils | utils.py | Hilfsfunktionen für Module |

### Backend-API-Routen (`backend/api/routes/`)

| Route | Datei | Zweck |
|-------|-------|-------|
| /api/actions | actions.py | Remote-Companion Aktionen |
| /api/devices | devices.py | Geräte-Verwaltung |
| /api/modules | modules.py | Module auflisten |
| /api/pairing | pairing.py | Remote Pairing |
| /api/sessions | sessions.py | Remote Sessions |
| /api/ws | ws.py | WebSocket |

### Backend-Core (`backend/core/`)

| Modul | Verantwortung |
|-------|----------------|
| settings.py | Remote-Companion-Defaults (REMOTE_FEATURE_ENABLED, etc.) |
| registry.py | Remote-Modul-Registry |
| auth.py | Authentifizierung |
| permissions.py | Berechtigungsprüfung |

### Backend-Services (`backend/services/`)

| Service | Verantwortung |
|---------|----------------|
| module_loader.py | Registrierung Remote-Module (SabrinaTuner, PiInstaller) |
| sabrina_tuner_service.py | DSI-Radio / Sabrina Tuner |
| pi_installer_service.py | PI-Installer als Remote-Modul |

### Backend-Storage (`backend/storage/`)

| Modul | Verantwortung |
|-------|----------------|
| db.py | Remote-DB (SQLite), init_remote_db |

### Frontend

| Bereich | Pfad | Beschreibung |
|---------|------|---------------|
| App | frontend/src/App.tsx | Routing, Plattformerkennung, DSI-Radio View |
| Pages | frontend/src/pages/ | Einzelne Screens (Dashboard, Settings, etc.) |
| Components | frontend/src/components/ | Wiederverwendbare UI-Komponenten |
| Context | frontend/src/context/ | PlatformContext, UIModeContext |
| Features | frontend/src/features/ | Remote-Companion (Pair, Dashboard, Module) |

---

## 2. Hauptpfade

### Startpfade

| Skript | Zweck |
|--------|-------|
| `start-backend.sh` | Backend (uvicorn) auf Port 8000 |
| `start.sh` | Backend + Frontend (npm run dev) |
| `start-setuphelfer.sh` | Wartet auf Backend, Dialog (Tauri/Browser); Alias `start-pi-installer.sh` |

### Konfigurationspfade

| Pfad | Verwendung |
|------|------------|
| `/etc/setuphelfer/config.json` | Primär (wenn schreibbar; Legacy: `/etc/pi-installer/`) |
| `~/.config/setuphelfer/config.json` | Fallback (User/Dev; Legacy: `pi-installer`) |
| `/etc/setuphelfer/debug.config.yaml` | Debug-Konfiguration (optional) |

### Persistenzpfade

| Pfad | Inhalt |
|------|--------|
| `logs/pi-installer.log` | Backend-Log (rotierend) |
| `data/` | App-Daten (z. B. dsi-radio-setup) |
| `backend/logs/` | Debug JSONL (wenn aktiv) |

---

## 3. Konfigurationsquellen

### Haupt-Konfiguration (config.json)

**Ladepfad:** `backend/app.py` – `_config_path()` → `_load_or_init_config()`

**Struktur:**
- `device_id`, `created_at`, `last_seen_at`
- `system`: hostname, model, os_release, kernel
- `settings`: ui, backup, logging, network, remote

**Erzeugung:**
- `scripts/install-system.sh` – legt config.json an
- `scripts/deploy-to-opt.sh` – legt config.json an

**Problem dokumentiert:**
- `debian/postinst` erzeugt noch **config.yaml** (Zeilen 39–50), wenn keine Config existiert
- Runtime liest ausschließlich **config.json**
- Folge: Bei Installation über .deb hat der Nutzer eine config.yaml, die das Backend ignoriert

### Debug-Konfiguration

**Layering:**
1. `backend/debug/defaults.yaml`
2. `/etc/pi-installer/debug.config.yaml` (optional)
3. ENV: `PIINSTALLER_DEBUG_ENABLED`, `PIINSTALLER_DEBUG_LEVEL`, `PIINSTALLER_DEBUG_PATH`

**Loader:** `backend/debug/config.py` – `load_debug_config()`, `get_effective_config_cached()`

---

## 4. Debugfluss

### Komponenten

| Komponente | Datei | Zweck |
|------------|-------|-------|
| Config | debug/config.py | Layering defaults → system → ENV |
| Logger | debug/logger.py | JSONL-Events, run_id, step_start/step_end |
| Context | debug/context.py | request_id (ContextVar) |
| Redaction | debug/redaction.py | Sensible Daten maskieren |
| Support Bundle | debug/support_bundle.py | Logs/Configs bündeln |
| Middleware | debug/middleware.py | RUN_START/RUN_END, request_id in Headern |
| Paths | debug/paths.py | Log-Pfad auflösen |
| Rotate | debug/rotate.py | Log-Rotation |

### Event-Typen

- `RUN_START`, `RUN_END`
- `STEP_START`, `STEP_END`
- `DECISION`, `APPLY_ATTEMPT`, `APPLY_NOOP`, `APPLY_SUCCESS`, `APPLY_FAILED`
- `ERROR`

### Konsistenz

- ENV-Namen: `PIINSTALLER_DEBUG_*` (nicht `PI_INSTALLER_DEBUG_CONFIG`)
- Schema v1 in debug.config.yaml, defaults.yaml

---

## 5. Initialisierungsreihenfolge

### Backend-Startup (`@app.on_event("startup")`)

| Schritt | Aktion |
|---------|--------|
| 1 | `init_debug()` |
| 2 | `run_start()` |
| 3 | `_load_or_init_config()` → config.json laden/initialisieren |
| 4 | `app.state.app_settings`, `app.state.device_id` setzen |
| 5 | `init_remote_db(CONFIG_PATH.parent)` (falls Remote feature) |
| 6 | Control-Center-Modul: `ensure_display_telemetry_autostart()` (OLED) |

### Shutdown

| Schritt | Aktion |
|---------|--------|
| 1 | `run_end()` mit duration_ms |

### Abhängigkeiten

- Config muss vor allen API-Handlern und vor Remote-DB geladen sein
- Remote-DB benötigt CONFIG_PATH.parent
- OLED-Autostart benötigt Control-Center-Modul (lazy geladen)

---

## 6. Dokumentierte strukturelle Probleme

| Problem | Ort | Risiko | Empfehlung |
|---------|-----|--------|------------|
| debian/postinst erzeugt config.yaml | debian/postinst Zeilen 39–50 | Systemweite Config kann wirkungslos bleiben (Runtime liest config.json) | postinst auf config.json umstellen (analog install-system.sh) |
| Bestehende config.yaml in /etc/pi-installer | Migration | Alte Installationen haben ggf. config.yaml, Backend ignoriert sie | Manuelle Migration oder Migrationsskript dokumentieren |
| Remote-DB Init optional | app.py | init_remote_db kann fehlschlagen, Backend läuft weiter | Bereits dokumentiert (Warning-Log) |

---

## 7. Zusammenfassung Phase 1

- **Modulverantwortlichkeiten:** Klar definiert, Backend-Module decken fachliche Bereiche ab
- **Hauptpfade:** start-backend.sh, config.json, Debug-Layering sind dokumentiert
- **Konfigurationsfluss:** config.json als einzige Runtime-Quelle, Debug separat
- **Debugsystem:** Einheitlich (Schema v1, ENV PIINSTALLER_DEBUG_*)
- **Initialisierung:** Ablauf in init_flow.md und config_flow.md beschrieben

**Empfohlene Nachbesserung (ohne großes Refactoring):**
- debian/postinst: config.yaml → config.json angleichen
