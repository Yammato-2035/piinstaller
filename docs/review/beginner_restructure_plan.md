## PI-Installer – Beginner-First Neuorganisation (Analysephase)

_Stand: 2026-03-10 – Phase 1: Nur Analyse, keine Code-Änderungen._

---

### 1. Aktuelle Architektur (High-Level)

- **Monolithisches Backend (`backend/`)**
  - Zentrale FastAPI-App in `backend/app.py` mit sehr vielen Endpunkten und Verantwortlichkeiten (Systeminfos, Backup, Security, Webserver, Mail, DevEnv, Control Center, Raspberry-Pi-Config, Remote-Companion, DSI-Radio-Integration, Debugging).
  - Modulschicht unter `backend/modules/` (z. B. `backup`, `control_center`, `devenv`, `mail`, `raspberry_pi_config`, `security`, `users`, `webserver`, `utils`) – teils angebunden, teils nur vorbereitet.
  - Remote-/Companion-Schicht (`backend/api/routes/*`, `backend/core/*`, `backend/services/*`, `backend/storage/db.py`) für „Linux Companion“ und Remote-Steuerung.
  - Debug-/Tracing-System (`backend/debug/*`) mit JSONL-Logs, Support-Bundle, Konfig-Layering.
  - Konfiguration primär über `config.json` (siehe `_config_path()` und `_load_or_init_config()` in `backend/app.py`), ergänzt um Debug-Config (`debug.config.yaml` + ENV).

- **React/Tauri-Frontend (`frontend/`)**
  - Einstieg über `frontend/src/main.tsx` (ReactDOM + `App`), Vite-Build (`vite.config.ts`), optional Tauri-Desktop-App (`frontend/src-tauri`).
  - Zentrale UI-Logik in `frontend/src/App.tsx`:
    - Verwalten des aktuellen „Page“-Strings (`currentPage`), Sidebar, Modals.
    - Ein großer Satz an Seiten („Setup-Seiten“): `Dashboard`, `SecuritySetup`, `UserManagement`, `DevelopmentEnv`, `WebServerSetup`, `MailServerSetup`, `NASSetup`, `HomeAutomationSetup`, `MusicBoxSetup`, `InstallationWizard`, `PresetsSetup`, `LearningComputerSetup`, `MonitoringDashboard`, `BackupRestore`, `SettingsPage`, `RaspberryPiConfig`, `ControlCenter`, `PeripheryScan`, `KinoStreaming`, `Documentation`, `AppStore`, `PiInstallerUpdate`, `TFTPage`, `DsiRadioSettings`, `RemoteView`.
  - Navigation über `Sidebar` (`frontend/src/components/Sidebar.tsx`), nicht über React-Router, sondern über „Page“-Enum + State.
  - Kontextschichten: `PlatformContext` (Plattform, Titel), `UIModeContext` (Grundlagen/Erweitert/Diagnose).
  - Remote-/Companion-UI unter `frontend/src/features/remote/*` (Pairing, Linux Companion).
  - Icon-/Designsystem bereits vorhanden (z. B. `frontend/dist/assets/icons/...`, `AppIcon`-Komponente), aber eher technisch/Modul-orientiert.

- **Apps (`apps/`)**
  - Spezielle Begleit-Apps wie `apps/dsi_radio/*` (DSI-Radio, QML/Qt + GStreamer-Player) und `apps/picture_frame/picture_frame.py` (Bilderrahmen).
  - Diese Apps nutzen das Backend teilweise (Metadaten, Konfiguration) und haben eigene Startpfade.

- **Skripte & Systemintegration (`scripts/`, `start*.sh`, `debian/*`)**
  - Startskripte:
    - `start-backend.sh`: Backend im Venv auf Port 8000.
    - `start.sh`: Backend + Frontend (Browser-Modus, Vite).
    - `start-frontend.sh`, `start-frontend-desktop.sh`, `start-pi-installer.sh`: verschiedene Kombi-Starter, inkl. Tauri-Integration und Desktop-Launcher.
  - Systeminstallation: `scripts/install-system.sh`, `scripts/deploy-to-opt.sh`, `debian/postinst`, systemd-Services (`pi-installer*.service`).
  - Diagnose-/Fix-Skripte (Display, Audio, Freenove, NVMe, etc.) – technisch orientiert, für Einsteiger schwer zu überblicken.

- **Dokumentation (`docs/`, `README*.md`)**
  - Umfangreiche technische Doku: Systeminstallation (`SYSTEM_INSTALLATION.md`), Audit-Report (`SYSTEM_AUDIT_REPORT.md`), Architektur (`docs/architecture/*`), Entwicklung (`docs/development/*`), Reviews (`docs/review/*`), Remote-Companion, Spezial-Apps etc.
  - Zusätzlich eine TSX-basierte Doku-Seite im Frontend (`Documentation.tsx`) – doppelte Pflege neben Markdown.

---

### 2. Module & Ein-/Ausgangspunkt-Übersicht

#### 2.1 Backend-Module (fachliche Bereiche)

Basierend auf `backend/modules/README.md` und den Audit-Dokumenten:

- **Backup (`backend/modules/backup.py`)**
  - Verantwortlich für Backup/Jobs, Klonen, ggf. Cloud-Integration.
  - Teile der Backup-Logik leben parallel in `backend/app.py` (D-006 im Audit).

- **Control Center (`backend/modules/control_center.py`)**
  - WLAN, SSH, VNC, Telemetrie, OLED, Lüfter, Peripherie.
  - Über `_get_control_center_module()` in `app.py` angebunden.

- **Dev-Umgebung (`backend/modules/devenv.py`)**
  - Entwicklungstools, Sprachen, Datenbanken, IDEs.
  - UI besitzt Endpunkte (`/api/devenv/configure`), Backend-Seite bislang nur TODO/teilweise (L-001).

- **Mail (`backend/modules/mail.py`)**
  - Mailserver-Konfiguration.
  - UI ruft `/api/mail/configure` auf, Backend-Seite ist unvollständig (L-002).

- **Raspberry Pi Config (`backend/modules/raspberry_pi_config.py`)**
  - `config.txt`, Overclocking, Overlays, EDID, UART, Display-Konfiguration.
  - Hoher Risikobereich (Bootloader-nah); bereits im Audit als sensibel markiert.

- **Security (`backend/modules/security.py`)**
  - Firewall (UFW), Fail2Ban, SSH-Härtung, Auto-Updates.
  - In Teilen doppelt zu inline-Security-Logik in `backend/app.py`.

- **Users (`backend/modules/users.py`)**
  - Benutzerverwaltung, sudo-Passwort-Session, User-spezifische Einstellungen.

- **Webserver (`backend/modules/webserver.py`)**
  - Nginx/Apache, Reverse-Proxy, Zertifikate.
  - Logik teilweise direkt in `backend/app.py`, Modul teils nicht voll angebunden.

- **Utils (`backend/modules/utils.py`)**
  - Hilfsfunktionen, Systembefehle, Abstraktionen für Shell-Aufrufe und Checks.

#### 2.2 Backend-Einstiegspunkte

- **Hauptapplikation**
  - `backend/app.py`:
    - Initialisierung (Logging, Debug, Config-Load, Remote-DB).
    - Alle API-Routen (`@app.get("/api/...")` / `@app.post(...)` etc.).
    - Systemkommandos via `subprocess`/`psutil`.
    - Remote-Companion-Einbindung.

- **Remote-/Companion-API**
  - `backend/api/routes/*` (z. B. `actions.py`, `devices.py`, `modules.py`, `pairing.py`, `sessions.py`, `ws.py`).
  - Wird über `app.include_router(...)` aus `app.py` eingebunden (Details in den Architektur-Docs).

- **Services**
  - `backend/services/pi_installer_service.py`, `sabrina_tuner_service.py`, `module_loader.py`: registrieren PI-Installer und DSI-Radio als Remote-Module.

- **Konfiguration & Debug**
  - Config:
    - `_config_path()` + `_load_or_init_config()` in `backend/app.py`.
    - Pfade: `/etc/pi-installer/config.json` (Primär), `~/.config/pi-installer/config.json` (Fallback).
  - Debug:
    - `backend/debug/config.py`, `backend/debug/logger.py`, `backend/debug/*`.

- **Startskripte (Backend-Seite)**
  - `start-backend.sh`: Startet uvicorn (`python -m uvicorn app:app --host ... --port 8000`).
  - Systemd: `pi-installer-backend.service`, `pi-installer.service` (über Install-Skripte generiert).

#### 2.3 Frontend-Einstiegspunkte

- **React-App**
  - `frontend/src/main.tsx`: ReactDOM-Root und Fehlergrenze (`ErrorBoundary`) → `App`.
  - `frontend/src/App.tsx`:
    - Verantwortlich für:
      - Seiten-State (`currentPage: Page` mit vielen Modul-Seiten).
      - Themenwahl (hell/dunkel/system).
      - Laden der Systeminfos (`/api/system-info`), Freenove-Detection.
      - Einbindung `Sidebar`, `SudoPasswordDialog`, `FirstRunWizard`, diverse Modals.
    - Steuert, welche Seite gerendert wird (z. B. `Dashboard`, `SecuritySetup`, `BackupRestore`, `DevelopmentEnv`, `MailServerSetup`, `ControlCenter`, `RemoteView` etc.).

- **Navigation / Sidebar**
  - `frontend/src/components/Sidebar.tsx`:
    - Listet Module (Dashboard, Linux Companion, App Store, Security, Users, DevEnv, Webserver, Mailserver, NAS, Home Automation, Musicbox, Kino/Streaming, Lerncomputer, Monitoring, Backup, Pi-Installer Update, Control Center, Peripherie-Scan, Raspberry Pi Config optional).
    - Modus-Schalter: Grundlagen / Erweitert / Diagnose via `UIModeContext`.
    - Versionanzeige (aktuell aus Build-Zeit-Variable).

- **Remote-/Linux Companion UI**
  - `frontend/src/features/remote/RemoteView.tsx` + Unterseiten (z. B. `PairPage.tsx`).
  - Ermöglicht Pairing, Fernzugriff, Projektauswahl.

- **Tauri/Desktop**
  - `frontend/src-tauri/*`: Rust-Tauri-Konfiguration, Icons, Bundling.
  - `tauri.conf.json` (wird über `sync-version.js` aktualisiert).

#### 2.4 Konfigurationsdateien und -quellen

- **Laufzeitkonfiguration**
  - `config.json` (systemweit):
    - Pfad: `/etc/pi-installer/config.json` (Hauptquelle), `~/.config/pi-installer/config.json` (Fallback).
    - Inhalt: `device_id`, Systeminfo, `settings` (UI, Backup, Logging, Network, Remote).
    - Erzeugt durch `scripts/install-system.sh` und `scripts/deploy-to-opt.sh`.
  - Debug-Konfiguration:
    - `backend/debug/defaults.yaml`, `backend/debug/debug.config.yaml`, ENV `PIINSTALLER_DEBUG_*`.

- **Versionen**
  - Aktuell (`Stand vor dieser Aufgabe`):
    - `VERSION` im Projekt- oder Installationsroot (z. B. `/opt/pi-installer/VERSION`).
    - `frontend/package.json` + `sync-version.js` → synchronisiert Version ins Frontend/Tauri.
    - Backend liest Version aus `VERSION` (ggf. mit ENV-Override).

- **Docs**
  - Zahlreiche `.md`-Dateien in `docs/` (Systeminstallation, Architekturbeschreibung, Audit, Pfade, Apps, Remote-Companion, Entwicklung).

---

### 3. Probleme für Einsteiger (Beginner-First-Sicht)

- **Zu viele gleichwertige Funktionen im Hauptmenü**
  - Sidebar und `App.tsx` präsentieren sehr viele Module gleichzeitig:
    - Security, Users, DevEnv, Webserver, Mailserver, NAS, Home Automation, Music Box, Kino/Streaming, Lerncomputer, Monitoring, Backup, Raspberry-Pi-Config, Control Center, Peripherie-Scan, App Store, Pi-Installer Update, DSI-Radio-Einstellungen, Remote, Doku.
  - Für Einsteiger entsteht der Eindruck eines „Administrations-Cockpits“ statt eines geführten Assistenten.
  - Es gibt keinen klaren Einstieg wie „Was möchtest du tun?“.

- **Technische Begriffswahl**
  - Begriffe wie „Dev-Umgebung“, „Mailserver“, „Webserver“, „Control Center“, „NAS“, „Docker“, „Reverse-Proxy“ sind für Einsteiger schwer einzuordnen.
  - Doku und UI verwenden Fachbegriffe (z. B. „Deploy“, „Repository“, „Debug“, „Service“, „Systemd“) ohne Übersetzung in Alltagssprache.

- **Gleiche visuelle Hierarchie für riskante und harmlose Aktionen**
  - Kritische Bereiche (Mailserver, Webserver, Raspberry-Pi-Config/Overclocking, Firewalls) erscheinen im UI auf ähnlicher Ebene wie harmlose Operationen (Backup, Updates, Monitoring).
  - Es gibt kein explizites Risikolevel oder visuelle Abgrenzung (z. B. Farbcodes, Warnhinweise vor Ausführung).

- **Parallel existierende Welten (Installer vs. Linux Companion vs. DSI-Radio vs. Spezial-Apps)**
  - `App.tsx` vereint:
    - klassischen PI-Installer (Setup-Seiten, Security, Webserver, Mailserver etc.),
    - Linux Companion (Remote-Features),
    - DSI-Radio/Sabrina-Tuner,
    - Spezialpfade (Bilderrahmen, TFT).
  - Für Einsteiger ist nicht klar, was der „Kern“ des Produkts ist und was Zusatzfunktionen sind.

- **Dokumentationsdoppelung und Einstiegshürden**
  - Markdown-Doku (`docs/*.md`) vs. TSX-Handbuch (`Documentation.tsx`).
  - README und Audit-Reports sind sehr detailliert und technisch – wertvoll für Entwickler, aber erschlagend für Einsteiger.
  - Es fehlt ein expliziter, sehr einfacher „Erste Schritte“-Pfad („Starte hier, wir prüfen dein System“).

---

### 4. UI-Komplexität – konkrete Beobachtungen

- **Seitenanzahl und Seitentypen**
  - Viele Seiten mit ähnlichem Muster: große Konfigurationskarte + Status, API-Call, Sudo-Dialog (z. B. SecuritySetup, WebServerSetup, MailServerSetup, NASSetup, HomeAutomationSetup, MusicBoxSetup).
  - Aus Beginner-Sicht erscheinen alle Seiten gleichberechtigt, obwohl deren Komplexität und Risiko stark variiert.

- **Navigation & Moduskonzept (`UIModeContext`)**
  - Es existiert bereits ein Modus-Schalter (Grundlagen / Erweitert / Diagnose), jedoch:
    - Ist der Zusammenhang zwischen User-Erfahrung und diesem Modus für Einsteiger nicht klar.
    - Die Zuordnung der Seiten in `Sidebar` und `App.tsx` zu den Modi ist vor allem technisch motiviert, nicht nach Lernkurve oder Risiko.

- **Erster Start / Wizard**
  - Es gibt bereits einen `FirstRunWizard`-Komponentenpfad (z. B. Einführung, Hinweise), der Zustand wird über `FIRST_RUN_DONE_KEY` in `localStorage` abgelegt.
  - Dieser Wizard ist jedoch nicht als „System-Check + Profilwahl“ mit klaren, sichtbaren Ergebnissen (Hardware, Netz, Erfahrungstyp) konzipiert, sondern eher als Einführungstext.

- **Fehlende Aufgabenorientierung**
  - Hauptbildschirm ist eher ein Dashboard/Modul-Listing als eine Aufgabenfrage.
  - Es gibt keine zentrale Frage wie „Was möchtest du tun?“ mit 5–6 klaren, großen Kacheln (Setup, Apps, Backup, Systemstatus, Lernen, Erweitert).

---

### 5. Konfigurations- und Sicherheitsaspekte (Beginner-Relevanz)

- **Konfigurationsquellen**
  - Aktuell ist `config.json` klar als Primärquelle definiert (Systemweit + Fallback), YAML wurde bereits zugunsten von JSON zurückgedrängt.
  - Gleichzeitig existieren noch ältere Doku- und Packaging-Pfade (`config.yaml` in `debian/postinst`), die Verwirrung stiften können (C-001).
  - Für Beginner-UX ist wichtig:
    - **Eine** sichtbare, erklärbare Konfigurationsquelle (z. B. „Profileinstellungen“ unter „Einstellungen“), die UI-Level (Beginner/Advanced/Developer), bevorzugte Sprache, Risiko-Toleranz etc. enthält.

- **Bootloader-nahe Bereiche**
  - `raspberry_pi_config` kann theoretisch seriöse Risiken erzeugen (Overclocking, config.txt, UART).
  - Prinzipien „Bootloader nie automatisch ändern“ und „keine Konfig-Duplikate“ passen bereits zu den bestehenden Audit-Empfehlungen (vorsichtige Behandlung dieser Module).

- **Idempotente Systemänderungen**
  - Viele Skripte und Routen wurden bereits auf Wiederholbarkeit geprüft (`install-system.sh`, Backup, Deploy nach `/opt`).
  - Für Einsteiger ist wichtig, dass jede große Aktion als „sicher wiederholbar“ und „rückverfolgbar“ (Logs) erklärt wird.

---

### 6. Empfohlene Umstrukturierung (nur Konzept, keine Umsetzung)

Hinweis: Diese Empfehlungen sind bewusst auf Beginner-First, reduzierte Komplexität und progressive Freischaltung ausgerichtet. Die spätere Umsetzung muss Anti-Regression-Regeln und bestehende Funktionen respektieren.

#### 6.1 Informationsarchitektur – von Modulen zu Aufgaben

- **Neues mental Model für die Startseite: „Was möchtest du tun?“**
  - Ersetzen des bisherigen Dashboard/Modul-Listings durch einen Aufgaben-basierten Home-Screen mit großen Karten:
    - „System einrichten“ (Setup-Wizard, Security-Grundlagen, Nutzer, Basisdienste).
    - „Apps installieren“ (App Store, vordefinierte „Projekt“-Bundles).
    - „Backup erstellen & wiederherstellen“ (BackupRestore).
    - „Systemzustand prüfen“ (Health Check, Monitoring light).
    - „Lernen & entdecken“ (Discovery-Mode: Projektideen).
    - „Erweiterte Funktionen“ (führt zu modularem Expertenbereich).

- **Module bleiben intern, werden aber thematisch gruppiert**
  - Security, Webserver, Mailserver, NAS, Home Automation, Music Box, Docker, DevEnv, Monitoring, Control Center, Raspberry-Pi-Config werden **nicht** einzeln im Hauptmenü angezeigt, sondern:
    - Über Aufgabenpfade erreichbar (z. B. „Heimserver einrichten“ → nutzt Webserver, NAS, Docker-Basis).
    - In Experten-Ansichten zusammengefasst (z. B. „Erweiterte Server-Funktionen“, „Entwickler-Werkzeuge“).

#### 6.2 UX-Level und progressive Freischaltung

- **Explizites User-Profil**
  - `config/user_profile.json` als logische Ergänzung zu `config.json`:
    - Felder: `experience_level` (Beginner/Advanced/Developer), bevorzugte Sprache, Lernziele.
  - UI:
    - Erster Start fragt: „Wie viel Erfahrung hast du mit Linux/Raspberry Pi?“.
    - Beginner sehen nur einen stark reduzierten Satz an Funktionen.
    - Advanced/Developer erhalten zusätzliche Karten/Module sichtbar geschaltet.

- **Integration mit bestehender UIMode-Logik**
  - `UIModeContext` (Grundlagen/Erweitert/Diagnose) kann als interne Darstellung genutzt werden.
  - Mapping:
    - Beginner → Grundlagen.
    - Advanced → Grundlagen + Erweitert.
    - Developer → alle + zusätzliche Dev-spezifische Wizards (Docker, DevEnv, Mailserver-Setup).

#### 6.3 Sidebar-Vereinfachung

- **Beginner-Ansicht**
  - Sidebar-Einträge auf wenige, klar benannte Punkte reduzieren:
    - Start
    - Setup-Wizard
    - Apps
    - Backup
    - Systemstatus
    - Hilfe
  - Alle anderen Module werden ausgeblendet, bleiben aber über Expertenpfade erreichbar, sobald der User-Level erhöht wurde.

- **Advanced-/Developer-Ansicht**
  - Zusätzliche Menüpunkte erscheinen, gruppiert nach Themen:
    - „Steuerzentrale / Control Center“, „Monitoring“, „Netzwerkwerkzeuge“, „Entwicklungsumgebung“, „Docker & Container“, „Mailserver & Webserver“, etc.

#### 6.4 Risikolevel & Sicherheitsindikatoren

- **Einführung eines einheitlichen Risikokonzepts**
  - Jede Seite / jedes Modul erhält ein Label:
    - **GRÜN** – sichere, eher lesende oder reversible Aktionen (Monitoring, Backup, Updates, Lerninhalte).
    - **GELB** – moderate Systemänderungen (Docker-Basisinstallation, NAS, Firewall-Konfiguration).
    - **ROT** – potenziell gefährliche Operationen (Mailserver-Setup für Internet, Boot-Konfiguration, Overclocking).
  - Darstellung:
    - Farbcodes, Warnbanner („Achtung, dies kann dein System dauerhaft verändern“), ggf. „Doppelte Bestätigung“ bei ROT.
  - Beginnt als rein visuelle Klassifizierung, kann später in Wizards und Selbsttests integriert werden.

#### 6.5 Wizard- und Tasksystem (Grundlage für weitere Phasen)

- **Erster Start-Wizard**
  - Schritt 1: Systemcheck (Pi-Modell, CPU, RAM, Speicher, Netzwerk; Ergebnis mit Icons und Klartext).
  - Schritt 2: Erfahrung/Profilwahl (Beginner/Advanced/Developer).
  - Schritt 3: Empfehlungskarten („Empfohlene erste Schritte“).

- **Tasks statt Einzelaktionen**
  - Interne Repräsentation von Handlungen als „Tasks“:
    - z. B. „System sichern“, „Heimserver aufsetzen“, „Entwicklungsumgebung vorbereiten“.
  - Jeder Task kann:
    - Aus mehreren Backend-Endpunkten / Shell-Skripten bestehen.
    - Einen Fortschrittsbalken und erklärende Texte liefern.

---

### 7. Zusammenfassung Phase 1 (Baseline für weitere Phasen)

- Die bestehende Architektur ist funktional sehr mächtig, aber stark modul-/technikgetrieben und für Einsteiger schwer navigierbar.
- Backend, Frontend, Apps, Skripte und Doku sind bereits gut strukturiert und dokumentiert, benötigen aber eine **Beginner-zentrierte Sicht** (Tasks, Profile, Risiko).
- Es existiert bereits viel Vorarbeit in den Audit- und Architektur-Dokumenten (Struktur, Konfigflüsse, Debug), die für eine sichere Neuorganisation genutzt werden kann.
- Nächste Schritte (spätere Phasen):
  - Projektstruktur im Repo nach den Zielordnern ausrichten (Backend/Frontend/Apps/Config/Docs/Scripts/Website/Assets).
  - Ein klares Versionierungssystem (`config/version.json`) als Single-Source-of-Truth einführen.
  - UI schrittweise von modulbasiert zu aufgabenbasiert umbauen, ohne bestehende Funktionen zu entfernen.
  - Sicherheits- und Risikoindikatoren in allen kritischen Bereichen sichtbar machen, bevor Wizards und fortgeschrittene Features aktiv implementiert werden.

