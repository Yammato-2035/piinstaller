## Architektur-Overview – PI-Installer

_Kurzüberblick für Entwickler – welche Hauptteile es gibt und wie sie zusammenspielen._

---

### 1. High-Level-Komponenten

- **Backend (`backend/`)**
  - FastAPI-Anwendung (`app.py`) als zentrales API-Gateway.
  - Fachliche Module unter `backend/modules/` (u. a. backup, control_center, devenv, mail, raspberry_pi_config, security, users, webserver, utils).
  - Debug-/Support-System unter `backend/debug/`.

- **Frontend (`frontend/`)**
  - React-App (Vite), Einstieg über `src/main.tsx` → `src/App.tsx`.
  - Seiten unter `src/pages/`, wiederverwendbare Bausteine unter `src/components/`.
  - Optionaler Tauri-Wrapper (Desktop-App) unter `src-tauri/`.

- **Systemintegration / Skripte (`scripts/`)**
  - Systemweite Installation in `/opt/setuphelfer/` (FHS-konform; Legacy vor 1.4.0: archivierter Ordnername „pi-installer“ unter `/opt`).
  - Start-/Installations-/Service-Skripte (`start-*.sh`, `install-system.sh`, `install-backend-service.sh` etc.).

- **Dokumentation (`docs/`)**
  - Unterteilt in user/ (Endnutzer), architecture/, developer/, design/, review/, testing/.

---

### 2. Daten- und Kontrollfluss (vereinfacht)

1. **Frontend → Backend**
   - HTTP-Requests von React (Fetch über `frontend/src/api.ts`) an FastAPI-Endpunkte (`/api/...`).
   - WebSockets für bestimmte Live-Funktionen (z. B. Remote/Companion).

2. **Backend → System**
   - Module rufen Systemkommandos/Skripte auf (z. B. Backup, ControlCenter, RaspberryPiConfig).
   - Konfiguration über Dateien (z. B. `config.json`), ENV und Debug-Config.

3. **System → Frontend**
   - Backend liefert Status-/Konfigurationsdaten (Systeminfo, Sicherheit, Dienste, Backups).
   - Frontend zeigt diese in Dashboard, Wizards und Einstellungsseiten an.

---

### 3. Wichtige Architektur-Dokumente

- `docs/architecture/ARCHITECTURE.md` – ausführliche Beschreibung der Komponenten und Flüsse.
- `docs/architecture/init_flow.md` – Start-/Init-Pfade (insbesondere für Systemd/Services).
- `docs/architecture/config_flow.md` – Konfigurationsflüsse (Dateien, ENV, Fallbacks).
- `docs/architecture/ui_modes.md` / `foundation_vs_advanced_map.md` – UI-Modi und Beginner-/Advanced-Sicht.
- `docs/architecture/PLAN.md`, `TRANSFORMATIONSPLAN.md`, `FINAL_SOLUTION.md` – historische/konzeptionelle Umbaupläne.

> Dieses Dokument ist ein Einstiegspunkt – Detailfragen sollten in den oben genannten Dateien nachgeschlagen werden.

---

### 4. Selbstprüfung (Phase 9 – Architektur-Overview)

- **Neue Funktionalität eingeführt?** – Nein, reine Zusammenfassung vorhandener Architektur-Docs.
- **Architektur geändert?** – Nein, nur beschrieben.

