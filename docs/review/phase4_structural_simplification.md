# Phase 4 – Strukturelle Systemvereinfachung

_Datum: 2026-03-09_

**Ergänzung 2026-04 (Setuphelfer 1.4.x):** Service- und Pfadnamen sind konsolidiert; maßgeblich für Reviews: **`docs/architecture/NAMING_AND_SERVICES.md`**. Die folgenden Abschnitte beschreiben die Ausgangslage und Maßnahmen bis März 2026 und können historische Begriffe (**pi-installer**-Units) enthalten.

## 1. Zielbild

- Zuständigkeiten klarer
- Doppelte Pfade dokumentiert und reduziert
- Konfigurationsquellen nachvollziehbar
- Debugging konsistent eingebunden
- Modulgrenzen verständlicher
- Wartbarkeit verbessert
- Vorbereitung Grundlagen / Erweitert

**Nicht:** Neu erfinden, verschönern, Featureumfang erweitern, funktional verändern.

---

## 2. Ausgangslage

Aus System Audit und Priorität-B-Fixes:

- Monolithisches `backend/app.py` (~11.200 Zeilen)
- `backend/modules/*`: teils aktiv (raspberry_pi_config, backup, control_center), teils ungenutzt (security, webserver, mail, devenv)
- Mehrere Konfigurationsquellen (config.json, debug YAML, ENV)
- Zwei Logging-Welten (klassischer Logger + backend/debug)
- Mehrere Service-Definitionen (pi-installer, pi-installer-backend)
- Setup-Seiten mit wiederholter Sudo-/Fetch-Logik
- Unklare Modulverantwortlichkeiten

---

## 3. Umgesetzte Vereinfachungen

| ID | Bereich | Vorher | Nachher | Nutzen | Risiko | Status |
|----|---------|--------|---------|--------|--------|--------|
| P4-01 | docs/architecture/ | Fehlend | config_flow.md, debug_flow.md, init_flow.md, foundation_vs_advanced_map.md | Konfig, Debug, Start und Grundlagen/Erweitert dokumentiert | keins | erledigt |
| P4-02 | backend/modules/README.md | Fehlend | Verantwortlichkeiten, aktiv vs. ungenutzt | Klarheit über Modulnutzung | keins | erledigt |
| P4-03 | Modulverantwortlichkeiten | Unklar | Pro Modul: Aufgabe, Abgrenzung, Abhängigkeiten | Wartbarkeit | keins | dokumentiert |

**Keine Code-Entfernung:** Ungenutzte Module (security, webserver, mail, devenv) bleiben – nur dokumentiert als STRUCTURE-MANUAL-REVIEW. Entfernung nur nach manueller Prüfung.

---

## 4. Geklärte Modulverantwortlichkeiten

| Modul | Aufgabe | Abgrenzung | Relevante Abhängigkeiten |
|-------|---------|------------|---------------------------|
| **app.py** | FastAPI-App, Endpoints, Config-Laden, Backup-Jobs, Run-Command, Remote-Router | Monolith; Fachlogik teils inline, teils über Module | debug, core, storage, api/routes |
| **modules/raspberry_pi_config** | Hardware-/Low-Level-Konfiguration (Overlays, EDID, Audio, Display) | Wird von app.py und control_center genutzt | SystemUtils |
| **modules/backup** | Backup-/Restore-Logik | Lazy über _get_backup_module() | – |
| **modules/control_center** | WLAN, SSH, VNC, Telemetrie, OLED, Lüfter | Lazy über _get_control_center_module() | raspberry_pi_config |
| **modules/security, webserver, mail, devenv** | Nicht von app.py genutzt | Logik lebt in app.py; Entfernung nur nach Prüfung | SystemUtils |
| **core/** | Eventbus, Registry, Auth, Permissions, QR | Unterstützend für Remote-Companion und App | – |
| **services/** | Remote-Companion-Module (pi_installer, sabrina_tuner) | Registriert in module_loader | core/eventbus |
| **debug/** | Debug-Config, Logger, Support-Bundle | Eigenständig; app.py nutzt init_debug, run_start, run_end | config.py, paths.py |

---

## 5. Vereinfachte Hauptpfade

### Konfiguration

- **Hauptpfad:** `config.json` über `_config_path()` / `_load_or_init_config()` in app.py
- **Keine Nebenzweige:** config.yaml wird nicht mehr verwendet (A-03)

### Debug

- **Hauptpfad:** `backend/debug/` – defaults → system → ENV
- **ENV:** PIINSTALLER_DEBUG_ENABLED, PIINSTALLER_DEBUG_LEVEL, PIINSTALLER_DEBUG_PATH

### Start

- **Backend:** start-backend.sh → uvicorn (Port 8000, PI_INSTALLER_BACKEND_PORT)
- **Kombi:** start-pi-installer.sh wartet auf Backend, dann Dialog (Tauri/Browser)

### Eventbus

- **Hauptpfad:** `publish_fire_and_forget()` aus core/eventbus (D-003)

---

## 6. Konfigurationsfluss

Siehe **docs/architecture/config_flow.md**

- **Primär:** /etc/pi-installer/config.json oder ~/.config/pi-installer/config.json
- **Debug:** defaults.yaml → /etc/pi-installer/debug.config.yaml → ENV
- **Keine .env-Ladung** in app.py (CONFIG.md dokumentiert, aber nicht verdrahtet)

---

## 7. Debugfluss

Siehe **docs/architecture/debug_flow.md**

- **Zentral:** debug/logger.py (init_debug, get_logger, run_start, run_end)
- **Modulabdeckung:** app.py, raspberry_pi_config
- **Altpfade:** print(), console.* – dokumentiert, nicht entfernt

---

## 8. Start-/Initialisierungsfluss

Siehe **docs/architecture/init_flow.md**

- **Reihenfolge:** init_debug → _load_or_init_config → init_remote_db → OLED-Autostart
- **Kritisch:** Keine Änderung an Boot-, Hardware-, Persistenzpfaden ohne Prüfung

---

## 9. Vorbereitung Grundlagen / Erweitert

Siehe **docs/architecture/foundation_vs_advanced_map.md**

- **Vorstrukturiert:** ControlCenter, RaspberryPiConfig, BackupRestore, Documentation, App-Navigation
- **Noch vermischt:** app.py Monolith, Setup-Seiten Copy-Paste
- **Keine UI-Änderung** in Phase 4

---

## 10. Verbleibende manuelle Risiken

| Bereich | Risiko | Maßnahme |
|---------|--------|----------|
| backend/modules security, webserver, mail, devenv | Ungenutzt, aber in __init__ | Nur nach Prüfung entfernen |
| app.py Monolith | Hohe Komplexität | Keine Aufteilung in Phase 4 |
| Service-Definitionen (pi-installer vs. pi-installer-backend) | Mehrere Pfade | Dokumentiert, nicht vereinheitlicht |
| Logpfad (pi-installer vs. piinstaller) | B-03 offen | Nicht angefasst |
| .env in CONFIG.md | Dokumentiert, nicht geladen | Klären oder Doku anpassen |

---

## Abschlussbericht

### Bereiche strukturell vereinfacht

1. Konfiguration: dokumentiert, Hauptpfad klar
2. Debug: dokumentiert, erlaubte/verbotene Pfade definiert
3. Initialisierung: dokumentiert, Reihenfolge festgehalten
4. Module: Verantwortlichkeiten und Nutzungsstatus dokumentiert
5. Grundlagen/Erweitert: Kandidaten kartiert

### Hauptpfade jetzt führend

- config.json (Runtime)
- backend/debug (Debug)
- start-backend.sh / start-pi-installer.sh (Start)
- publish_fire_and_forget (Eventbus)

### Konfigurationsquellen maßgeblich

- config.json über _config_path()
- Debug: defaults → system → ENV

### Debugpfade verbindlich

- init_debug, run_start, run_end, get_logger
- Kein print() im Produktivpfad (Ziel)

### Bereiche mit manueller Vorsicht

- Ungenutzte Module entfernen
- app.py aufteilen
- Service-Definitionen vereinheitlichen
- Boot-/Hardware-/Storage-Logik

### Die 10 wichtigsten strukturellen Verbesserungen

1. config_flow.md – Konfigurationsfluss dokumentiert
2. debug_flow.md – Debugpfade und Modulabdeckung dokumentiert
3. init_flow.md – Startreihenfolge und kritische Bereiche dokumentiert
4. foundation_vs_advanced_map.md – Grundlagen/Erweitert vorstrukturiert
5. backend/modules/README.md – Modulverantwortlichkeiten und Nutzungsstatus
6. Klare Hauptpfade: config.json, backend/debug, start-backend
7. Modulkatalog: aktiv vs. ungenutzt
8. Keine riskanten Code-Entfernungen
9. Dokumentation als zentrale Referenz
10. Vorbereitung für Phase 5/6 (UI-Trennung, UX)

### Die 5 größten verbleibenden Komplexitätsrisiken

1. **app.py Monolith** – ~11.200 Zeilen, viele Domänen
2. **Ungenutzte Module** – security, webserver, mail, devenv in __init__, nicht von app.py
3. **Zwei Logging-Welten** – klassischer Logger + debug
4. **Service-Definitionen** – pi-installer vs. pi-installer-backend
5. **Setup-Seiten Copy-Paste** – Sudo-, Fetch-, Konfig-Logik wiederholt
