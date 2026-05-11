## Backend-Struktur – Schnellüberblick

_Zweck: Orientierung für Entwickler im FastAPI-Backend._

---

### 1. Verzeichnisbaum (vereinfacht)

```text
backend/
  app.py                 # Haupt-FastAPI-App, API-Routen, Moduleinbindung
  modules/               # Fachmodule (Backup, ControlCenter, DevEnv, Mail, Security, Users, Webserver, RaspberryPiConfig, Utils)
  debug/                 # Debug-/Logging-/Support-Bundle-System
  api/                   # (sofern vorhanden) zusätzliche API-Routen, z. B. für Remote/Companion
  ...
```

Details siehe `docs/architecture/ARCHITECTURE.md` und `docs/architecture/init_flow.md`.

---

### 2. Hauptkomponente `app.py`

- Initialisiert:
  - FastAPI-App.
  - Logging/Debug-Konfiguration (`backend/debug`).
  - Konfiguration (z. B. `config.json`, ggf. Pfade unter `/etc/pi-installer/`).
- Bindet ein:
  - System-Info-Endpunkte (`/api/system-info`, `/api/system/...`).
  - Modulbezogene Endpunkte (Backup, Security, DevEnv, Webserver, Mail, Users, RaspberryPiConfig, ControlCenter, etc.).
  - Remote-/Companion-APIs (über `backend/api/routes/...`, sofern konfiguriert).

---

### 3. Module unter `backend/modules/` (Auszug)

- `backup.py` – Backup-/Job-Handling, Integration mit Scripts.
- `control_center.py` – WLAN, SSH, VNC, Telemetrie, OLED, Lüfter.
- `devenv.py` – Entwicklungsumgebung (Sprachen, Tools, DBs).
- `mail.py` – Mailserver-Konfiguration (Postfix/Dovecot etc.).
- `raspberry_pi_config.py` – Pi-spezifische Konfig (config.txt, Overclocking, Displays).
- `security.py` – Firewall, Fail2Ban, SSH-Härtung, Auto-Updates, Audit-Logging.
- `users.py` – Benutzer- und Sudo-Passwort-Verwaltung.
- `webserver.py` – Webserver-/Reverse-Proxy-Konfiguration.
- `utils.py` – Hilfsfunktionen/Systemkommandos.

Die genaue Verantwortung der Module ist in `backend/modules/README.md` und diversen Architektur-/Audit-Dokumenten beschrieben.

---

### 4. Debug-/Support-Bundle (`backend/debug/`)

- Konfiguration:
  - `backend/debug/config.py`, `defaults.yaml`, optionale `/etc/pi-installer/debug.config.yaml`, ENV-Variablen.
- Logging:
  - JSONL-Logs mit `run_id`/`request_id`, Scopes, Events (siehe README im Debug-Verzeichnis).
- Support-Bundle:
  - CLI/Helper zum Erstellen eines Support-Bundles (Logs, System-Snapshot, effektive Config).

Hinweis: Einige Pfade hier sind in Audit-Dokumenten als kritisch markiert; Details siehe `docs/SYSTEM_AUDIT_REPORT.md` und `docs/review/error_backlog_current_state.md`.

---

### 5. Systemintegration

- systemd-Service:
  - `pi-installer-backend.service` (Root des Repos) wird durch Skripte installiert.
- Skripte:
  - `scripts/install-backend-service.sh`, `scripts/install-system.sh`, `scripts/start-backend.sh` etc. setzen Umgebungen, Pfade und Dienste auf.

Weitere Details: `docs/SYSTEM_INSTALLATION.md`, `docs/PACKAGING.md`, `docs/SD_CARD_IMAGE.md`.

---

### 6. Selbstprüfung (Phase 9 – Backend-Struktur)

- **Nur Struktur dokumentiert?** – Ja, keine Änderungen an Backend-Code.
- **Keine neue Fehlerbehandlung/Features?** – Ja, nur Orientierungstext.

