# Changelog

Alle wichtigen ùnderungen am PI-Installer werden hier dokumentiert.  
Details und Versionsschema: [docs/developer/VERSIONING.md](./docs/developer/VERSIONING.md).

---

## [1.3.9.0] - 2026-04-03

### Added
- **Gef¸hrte Nutzung (Frontend):** Zentrales Modul- und Bereichsmodell (`frontend/src/beginner/moduleModel.ts`), wiederverwendbare Marker f¸r ÑGesperrt / Sp‰ter / Fortgeschrittenì (`BeginnerGuidanceMarker`).
- **Dashboard (Einsteiger):** Hervorgehobener Block ÑN‰chster sinnvoller Schrittì, empfohlene Aktionen, getrennte Bereiche f¸r optional und sp‰tere Module.
- **App Store (Einsteiger):** Empfohlene Apps zuerst, Hinweis-Badges und sortierte Darstellung.
- **Backup (Einsteiger):** Drei klare Einstiege (erstellen, pr¸fen, wiederherstellen); erweiterte Tabs unter ÑWeitere Optionenì.
- **Dokumentation:** `docs/user/GUIDED_UX_AND_COMPANION.md`; Handbuchtexte und **FAQ** in der App (Erfahrungslevel, Panda-Begleiter, Einsteigerf¸hrung); Eintrag im Kapitel **Einstellungen** (Erfahrungslevel).
- **Desktop:** `SetupHelfer.desktop` mit Logo-Icon; Starter `scripts/start-pi-installer.sh` mit Auswahl **Tauri / Browser / Nur Backend**; Debian- und Install-Skripte angepasst.
- **Profil-API:** Schreib-Fallback f¸r `user_profile.json` unter `~/.config/pi-installer/`, wenn `/etc/pi-installer/` nicht beschreibbar ist; Frontend wertet FastAPI-`detail` bei Fehlern aus.

### Changed
- **Version:** Kanonisch `1.3.9.0` in `config/version.json`; `sync-version.js` synchronisiert auch die Root-`package.json`.
- **Navigation (Einsteiger):** Optional Badge ÑFortgeschrittenì bei Monitoring in der Sidebar.

---

## [1.3.8.4] - 2026-04-03

### Changed
- Versionsnummer auf 1.3.8.4 angehoben (kanonisch `config/version.json`).

---

## [1.3.8.1] - 2026-03-12

### Added
- **Sicherheit:** CORS auf konfigurierbare Origins beschrùnkt (Standard: localhost; LAN ùber `PI_INSTALLER_CORS_ORIGINS`).
- **Sicherheit:** Sudo-Passwort nur noch verschlùsselt (Fernet) im Speicher, TTL 30 Min; Key in Installationsverzeichnis oder `~/.config/pi-installer/`.
- **Sicherheit:** Rate-Limiting auf `/api/users/sudo-password` (10/Min); Security-Header (X-Content-Type-Options, X-Frame-Options, Referrer-Policy).
- **Sicherheit:** Systemd-Services gehùrtet (ProtectSystem=strict, PrivateTmp, NoNewPrivileges, MemoryMax, LimitNOFILE).
- **Doku:** SECURITY.md (Netzwerk LAN/Internet, VPN-Empfehlung, Firewall); docs/user/NETWORK_ACCESS.md.
- **Version:** Einzige Quelle `config/version.json`; sync-version.js schreibt auch VERSION, package.json, Tauri.

### Changed
- Versionsnummer auf 1.3.8.1 angehoben (Patch: Security & Repo-Optimierungen).

---

## [1.3.8.0] - 2026-03-06

### Added
- **Remote Companion (Phase 1) ù Dokumentation:** ùbersicht und Architektur in `docs/REMOTE_COMPANION.md` (API, Rollen, Events, Datenmodell, Phase-2-Ausblick). Entwicklerleitfaden in `docs/REMOTE_COMPANION_DEV.md` (Modul registrieren, Widgets, Aktionen, Eventbus). Verweise in README und In-App-Dokumentation.
- Phase-2-Vorbereitung konzeptionell beschrieben: Sync-Status, Ordner-Profile, CalDAV/CardDAV-Healthcheck als spùtere Integrationspunkte (ohne Implementierung).

### Changed
- Versionsnummer auf 1.3.8.0 angehoben (neues Feature: Remote-Companion-Dokumentation).

---

## [1.3.7.6] - 2026-03-05

### Fixed
- OLED-Erkennung im Control Center auf `i2cdetect -r` umgestellt, damit keine falschen OLED-Treffer auf ungeeigneten I2C-Bussen mehr gemeldet werden.
- Hardware-Diagnose ergùnzt: Wenn `dtparam=i2c_arm=on` fehlt und `/dev/i2c-1` nicht existiert, wird klarer, warum der Runner kein OLED erreichen kann.

---

## [1.3.7.5] - 2026-03-05

### Fixed
- OLED-Telemetrie-Endpunkte im Backend wiederhergestellt (`/api/control-center/display/telemetry` und Runner-Action-Endpunkt), damit die OLED-Anzeige im Control Center wieder korrekt geladen und gesteuert werden kann.
- OLED-Autostart beim Backend-Start wieder aktiviert, sodass die Anzeige nach einem Neustart automatisch anlaufen kann.
- OLED-I2C-Erkennung auf variable Busse erweitert (`/dev/i2c-*` statt hart nur Bus 1), damit die Anzeige auch auf Systemen mit anderen I2C-Busnummern wieder gefunden wird.

---

## [1.3.7.4] - 2026-03-05

### Added
- Skript **backup-sd-card.sh**: Sicherheits-Backup der SD-Karte (Boot + Root), optional Ziel NVMe (`--nvme`) mit ext4 fùr vollstùndiges Backup
- Doku **NVME_BOOT_FREENOVE_SWITCH.md**: Boot von NVMe hinter Freenove-PCIe-Switch, EEPROM, UART-Debug, SD-Backup-Hinweise
- Verweise auf NVMe-Boot-Freenove in NVME_FULL_BOOT.md und PATHS_NVME.md

### Changed
- backup-sd-card.sh: Unterstùtzung fùr Zielfs ext4 (volle rsync-Optionen) bzw. vfat (eingeschrùnkt)
- Sync mit GitHub: Stand origin/main (1.3.4.15) integriert, lokale ùnderungen (Backup, NVMe-Docs) beibehalten

---

## [1.3.4.15] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.15

### Changed
- Build-Prozess optimiert


## [1.3.4.14] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.14

### Changed
- Build-Prozess optimiert


## [1.3.4.13] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.13

### Changed
- Build-Prozess optimiert


## [1.3.4.12] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.12

### Changed
- Build-Prozess optimiert


## [1.3.4.11] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.11

### Changed
- Build-Prozess optimiert


## [1.3.4.10] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.10

### Changed
- Build-Prozess optimiert


## [1.3.4.9] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.9

### Changed
- Build-Prozess optimiert


## [1.3.4.8] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.8

### Changed
- Build-Prozess optimiert


## [1.3.4.7] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.7

### Changed
- Build-Prozess optimiert


## [1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.6

### Changed
- Build-Prozess optimiert


## [1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:51:30][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:51:30][0m Aktuelle Version: 1.3.4.8
[0;32m[2026-02-16 16:51:30] ?[0m Version erhùht: 1.3.4.8 -> 1.3.4.9
[0;32m[2026-02-16 16:51:30] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:51:30] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.9] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:51:30][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:51:30][0m Aktuelle Version: 1.3.4.8
[0;32m[2026-02-16 16:51:30] ?[0m Version erhùht: 1.3.4.8 -> 1.3.4.9
[0;32m[2026-02-16 16:51:30] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:51:30] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.9

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:47:56][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:47:56][0m Aktuelle Version: 1.3.4.7
[0;32m[2026-02-16 16:47:56] ?[0m Version erhùht: 1.3.4.7 -> 1.3.4.8
[0;32m[2026-02-16 16:47:56] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:47:56] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.8] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:47:56][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:47:56][0m Aktuelle Version: 1.3.4.7
[0;32m[2026-02-16 16:47:56] ?[0m Version erhùht: 1.3.4.7 -> 1.3.4.8
[0;32m[2026-02-16 16:47:56] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:47:56] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.8

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:47:14][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:47:14][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:47:14] ?[0m Version erhùht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:47:14] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:47:14] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.7] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:47:14][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:47:14][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:47:14] ?[0m Version erhùht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:47:14] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:47:14] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.7

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:46:47][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:46:47][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:46:47] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:46:47] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:46:47] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:46:47][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:46:47][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:46:47] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:46:47] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:46:47] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:44:28][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:44:28][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:44:28] ?[0m Version erhùht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:44:28] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:44:28] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.7] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:44:28][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:44:28][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:44:28] ?[0m Version erhùht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:44:28] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:44:28] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.7

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:41:24][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:41:24][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:41:24] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:41:24] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:41:24] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:41:24][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:41:24][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:41:24] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:41:24] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:41:24] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:39:06][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:39:06][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:39:06] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:39:06] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:39:06] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:39:06][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:39:06][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:39:06] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:39:06] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:39:06] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:38:32][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:38:32][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:38:32] ?[0m Version erhùht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:38:32] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:38:32] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
[sync-version] version -> 1.3.4.7
1.3.4.7] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:38:32][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:38:32][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:38:32] ?[0m Version erhùht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:38:32] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:38:32] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
[sync-version] version -> 1.3.4.7
1.3.4.7

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:35:29][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:35:29][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:35:29] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:35:29] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:35:29] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:35:29][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:35:29][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:35:29] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:35:29] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:35:29] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:32:16][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:32:16][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:32:16] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:32:16] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:32:16] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
[sync-version] version -> 1.3.4.6
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:32:16][0m Schritt 1: Version erhùhen...
[0;36m[2026-02-16 16:32:16][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:32:16] ?[0m Version erhùht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:32:16] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:32:16] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
[sync-version] version -> 1.3.4.6
1.3.4.6

### Changed
- Build-Prozess optimiert


## [1.3.4.2] ù 2026-02

### DSI Radio (v2.1.0) ù NDR-Ton, Backend, Doku

- **NDR 1 / NDR 2 ù Ton funktioniert:** Die App bevorzugt jetzt getestete Stream-URLs aus `stations.py` (icecast.ndr.de). Wenn NDR 1 oder NDR 2 aus der Sendersuche stammen, werden die oft fehlerhaften addradio.de-URLs durch die funktionierenden icecast-URLs ersetzt. Siehe FAQ: ùNDR 1 / NDR 2: Kein Tonù.
- **Audio-Ausgabe auf dem Laptop:** Der explizite Pulse-Sink wird nur noch auf dem Freenove-Gerùt gesetzt. Auf dem Linux-Rechner nutzt GStreamer das System-Standard-Ausgabegerùt ù kein erzwungener Sink mehr, Ton lùuft ùber das gewùhlte Gerùt.
- **Backend-Start (PEP 668):** `start-backend.sh` und `start.sh` verwenden durchgùngig die Venv im Backend-Verzeichnis (`venv/bin/python3`, `venv/bin/pip`). Kein ùexternally-managed-environmentù-Fehler mehr bei System-Python 3.12+.
- **DSI Radio ù Anweisungen:** Fehlermeldungen und README nennen jetzt ùim Terminal auf dem Linux-Rechnerù, Beispielpfad `/home/volker/piinstaller`, Aufruf mit `sudo bash ù` bei ùBefehl nicht gefundenù. Backend-Hinweis fùr Logos/Sendersuche ergùnzt.
- **FAQ:** Neuer Eintrag ùNDR 1 / NDR 2: Kein Tonù (Stream-URL-Preferenz aus stations.py).

### Dokumentation

- **apps/dsi_radio/README.md:** Linux-Terminal-Anweisungen, Backend fùr Logos/Sendersuche, ùBefehl nicht gefundenù mit `sudo bash` und Zeilenumbrùche.
- **docs/START_APPS.md:** Backend manuell im Terminal starten (z. B. Laptop); DSI-Radio-Bedarf am Backend erwùhnt.

---

## [1.3.4.1] ù 2026-02

### Radio-App (DSI Radio) ù Metadaten-Verbesserungen

- **System-Metadaten aus PulseAudio/PipeWire:** Die App liest jetzt Titel/Interpret direkt aus dem Lautstùrkeregler-System (PulseAudio/PipeWire) ù dieselbe Quelle wie der System-OSD. Fallback wenn Backend/GStreamer keine Metadaten liefern.
- **"Es lùuft:" immer sichtbar:** Die Zeile "Es lùuft:" bleibt immer sichtbar, auch wenn kein Sendungsname vorliegt (zeigt dann nur "Es lùuft:" ohne Text dahinter).
- **Logo und Sendername beim Wiederherstellen:** Beim App-Start wird der zuletzt angehùrte Sender korrekt wiederhergestellt ù Logo und Sendername werden sofort aktualisiert.
- **Show-Metadaten-Erkennung:** Sendungsnamen wie "Die Show" oder "1LIVE Liebesalarm" werden automatisch als Show-Metadaten erkannt und erscheinen hinter "Es lùuft:", nicht mehr als Titel/Interpret.
- **Interpret-Textgrùùe:** Interpret-Label hat jetzt die gleiche Schriftgrùùe wie der Titel (14 statt 13), bleibt aber nicht fett dargestellt.

---

## [1.3.4.0] ù 2026-02

### Systemweite Installation gemùù Linux FHS

- **Neue Installationsmethode:** Systemweite Installation nach `/opt/pi-installer/` gemùù Linux Filesystem Hierarchy Standard (FHS)
- **Installations-Skripte:**
  - `scripts/install-system.sh` ù Systemweite Installation nach `/opt/pi-installer/`
  - `scripts/update-system.sh` ù Update-Skript fùr bestehende Installationen
  - `scripts/install.sh` ù Wrapper mit interaktiver Auswahl zwischen beiden Methoden
- **Installationsverzeichnisse:**
  - Programm: `/opt/pi-installer/`
  - Konfiguration: `/etc/pi-installer/`
  - Logs: `/var/log/pi-installer/`
  - Symlinks: `/usr/local/bin/` (globale Befehle wie `pi-installer`, `pi-installer-backend`)
- **Umgebungsvariablen:** Automatisch in `/etc/profile.d/pi-installer.sh` gesetzt
- **systemd Service:** Verbesserte Sicherheitseinstellungen (NoNewPrivileges, PrivateTmp, ProtectSystem)
- **Dokumentation:** Neue Dokumentation `docs/SYSTEM_INSTALLATION.md` mit vollstùndiger Anleitung
- **GitHub-Integration:** Alle Installations-Skripte direkt von GitHub verfùgbar ùber Raw-URLs

### Dual Display X11 ù Frùhe Konfiguration

- **LightDM Integration:** Verwendet `session-setup-script` fùr frùhe Display-Konfiguration nach Login
- **Position korrekt:** DSI-1 wird zuerst gesetzt (links unten 0x1440), dann HDMI-1-2 (rechts oben 480x0)
- **Keine mehrfachen Umschaltungen:** Atomare Konfiguration in einem xrandr-Befehl
- **Alte Skripte deaktiviert:** Automatische Deaktivierung von `enable-hdmi.sh` und verzùgerten Autostart-Skripten
- **Skript:** `scripts/fix-gabriel-dual-display-x11-early.sh` fùr optimierte frùhe Konfiguration

---

## [1.3.3.0] ù 2026-02

### Dual Display X11 ù stabil ohne stùndiges Umschalten

- **Stand:** DSI + HDMI unter X11 lùuft jetzt richtig; Position (DSI links unten, HDMI rechts oben), Desktop/Hintergrund auf HDMI (Primary), keine stùndige Umschaltung mehr.
- **Maùnahmen:** Atomarer xrandr-Befehl (beide Ausgaben in einem Aufruf); .xprofile setzt Layout nach 8 s und startet ~10 s nach Login PCManFM-Desktop neu (Trigger: Desktop ? Primary/HDMI); delayed-Script wendet Layout nach 8 s und 16 s an; optional `fix-desktop-on-hdmi-x11.sh` zum manuellen Neustart des Desktops.
- **Dokumentation:** [docs/DSI_HDMI_SPIEGELUNG_X11.md](docs/DSI_HDMI_SPIEGELUNG_X11.md) ù Spiegelung, Position, Desktop auf HDMI, Trigger, Beschleunigung (~10 s), FAQ-Verweise.
- **FAQ:** Eintrag ùDual Display X11 (DSI + HDMI) ù Desktop auf HDMI, stabilù ergùnzt; bestehender Eintrag zur DSI-Spiegelung beibehalten.

---

## [1.3.2.0] ù 2026-02

### Dual Display X11 ù DSI-Spiegelung auf HDMI

- **Problem:** Der komplette DSI-1-Desktop wurde oben links auf HDMI-1-2 gespiegelt (nicht nur ein Fenster). Ursache: Pi-KMS/DRM-Treiber legt die HDMI-Scanout-Region nicht korrekt ab Offset (480,0).
- **Maùnahmen in Scripts:** Explizite Framebuffer-Grùùe `xrandr --fb 3920x2240`; Konfiguration **HDMI vor DSI** (HDMI 480x0, dann DSI 0x1440). Angepasst: `fix-gabriel-dual-display-x11.sh`, `.xprofile`, `.screenlayout`, `apply-dual-display-x11-delayed.sh`, `fix-dsi-position-x11.sh`.
- **Dokumentation:** [docs/DSI_HDMI_SPIEGELUNG_X11.md](docs/DSI_HDMI_SPIEGELUNG_X11.md) ù Problem, umgesetzte Maùnahmen, optionale config.txt-Workarounds, manuelle Tests.
- **FAQ:** Neuer Eintrag ùDSI-Desktop oben links auf HDMI gespiegelt (X11)ù in der App-Dokumentation (Dokumentation ? FAQ) und Verweis in docs/VIDEO_TUTORIALS.md.

---

## [1.3.1.0] ù 2026-02

### Backup & Restore ù Laufwerk klonen & NVMe

- **Laufwerk klonen:** Neue Funktion in Backup & Restore ù System von SD-Karte auf NVMe/USB-SSD klonen (Hybrid-Boot: Kernel von SD, Root von NVMe). rsync-basiert, fstab und cmdline.txt werden automatisch angepasst.
- **NVMe-Erkennung:** Ziel-Laufwerke (NVMe, USB, SATA) werden ùber disk-info API erkannt und im Clone-Tab angezeigt. Modell, Grùùe und Mount-Status sichtbar.
- **Festgestellte Probleme:** Siehe Dokumentation ? FAQ fùr bekannte Einschrùnkungen und Lùsungswege (z.?B. NVMe-Pfade nach Clone, Dualdisplay-Konfiguration, Freenove-Case-Anpassungen).

### DSI-Radio (Freenove TFT ù native PyQt6-App)

- **Lautstùrke:** Regler steuert den aktiven Kanal (PulseAudio: `pactl set-sink-volume @DEFAULT_SINK@`; Fallback: ALSA amixer Master/PCM). Regler rechts neben Senderbuttons, oberhalb des Seitenumschalters (1/2 ?), silber umrandet.
- **Radioanzeige:** Logo links (96ù96), rechts schwarzer Klavierlack-Rahmen mit leuchtend grùner Anzeige und schwarzer Schrift; Schlieùen-Button (?) in der Anzeige; Uhr mit Datum, kompakt.
- **D/A-Umschalter:** Langgestrecktes rotes O mit rundem schwarzem Schieber, D (Digital/LED) und A (Analog); analoge VU-Anzeige mit Skala 0ù100 %, rechts roter Bereich, Zeiger begrenzt durch Lautstùrke.

### Dokumentation

- **Neue Bereiche:** ùFreenove Pro ù 4,3? Touchscreen im Gehùuseù und ùDualdisplay DSI0 + HDMI1 ù Zwei Monitore gleichzeitigù mit Tips & Tricks.
- **Lernbereich:** Themenblock ùTouchscreen am DSI0 Portù ergùnzt.
- **FAQ:** Aus Troubleshooting eine vollstùndige FAQ mit Fehlername, Beschreibung und Lùsungen; funktionales Design mit logischer Farbgebung; FAQ-Eintrag ùDSI-Radio: Lautstùrke funktioniert nichtù ergùnzt.

---

## [1.3.0.1] ù 2026-02

### Backup & Restore

- **Cloud-Backups lùschen:** Lùschung von Cloud-Backups (WebDAV/Seafile) funktioniert; URL-Konstruktion aus PROPFIND-`href` korrigiert (`base_domain + href`); Debug-Info in Response fùr Fehlerfùlle.
- **USB ? Cloud Wechsel:** Beim Wechsel von USB zu Cloud und zurùck werden die Backups des zuvor gemounteten USB-Sticks wieder geladen; `loadBackups(dirOverride)` und explizites Setzen von `backupDir` + Aufruf beim USB-Button.
- **Kein Cloud-Upload bei USB-Ziel:** Backups mit Ziel USB-Stick werden nicht mehr zusùtzlich in die Cloud hochgeladen; Backend lùdt nur noch bei `target` `cloud_only` oder `local_and_cloud`, nicht bei `local`.

---

## [1.3.0.0] ù 2026-02

### Transformationsplan: ùRaspberry Discovery Boxù

- **App Store:** Neue Seite mit 7 Apps (Home Assistant, Nextcloud, Pi-hole, Jellyfin, WordPress, VS Code Server, Node-RED); Kachel-Layout, Suche, Kategorien; Ein-Klick-Installation (API vorbereitet, Implementierung folgt).
- **First-Run-Wizard:** Beim ersten Start: Willkommen ? Optional (Netzwerk/Sicherheit/Backup) ? ùWas mùchtest du tun?ù (Smart Home, Cloud, Medien, Entwickeln) ? Empfohlene Apps ? App Store.
- **Dashboard-Redesign:** Hero ùDein Raspberry Pi lùuft!ù, groùer Status (Alles OK / Aktion benùtigt), Ressourcen-Ampel (CPU/RAM/Speicher), Schnellaktionen (Neue App installieren, Backup erstellen, System updaten).
- **Mobile:** Hamburger-Menù auf kleinen Screens; Sidebar als Overlay; touch-freundlich; responsive Padding.
- **Kontextsensitive Hilfe:** HelpTooltip-Komponente (?-Icon) an Dashboard und App Store.
- **Einstellungen:** Option ùErfahrene Einstellungen anzeigenù (versteckt; blendet Grundlegende Einstellungen und Dokumentations-Screenshots ein).
- **Fehlerfreundliche Texte:** App-Store-Installation: ùHuch, das hat nicht geklappt ùù statt technischer Fehlermeldung.
- **Installer & Docs:** Single-Script-Installer (`create_installer.sh`), systemd-Service (`pi-installer.service`), One-Click-Dokumentation (get.pi-installer.io); Python 3.9+ in Doku und requirements.

---

## [1.2.0.6] ù 2026-02

### NAS: Duplikat-Finder (Phase 1)

- **Duplikate & Aufrùumen:** Neuer Bereich in der NAS-Seite ù fdupes/jdupes installieren, Verzeichnis scannen, Duplikate in Backup verschieben (statt lùschen).
- **Installation:** Fallback auf jdupes, wenn fdupes nicht verfùgbar; klarere Fehlermeldungen von apt.
- **Scan:** Vorgeschlagener Pfad (Heimatverzeichnis, wenn /mnt/nas nicht existiert); Option ùSystem-/Cache-Verzeichnisse ausschlieùenù (.cache, mesa_shader, __pycache__, node_modules, .git, Trash) ù Standard: an.
- **API:** `POST /api/nas/duplicates/install`, `POST /api/nas/duplicates/scan`, `POST /api/nas/duplicates/move-to-backup`.
- **Dokumentation:** INSTALL.md ù Troubleshooting Duplikat-Finder-Installation; NAS-Dokumentation um Duplikate-Bereich ergùnzt.

---

## [1.2.0.5] ù 2026-02

### Dokumentation

- **Raspberry Pi 5: Kein Ton ùber HDMI** ù Troubleshooting erweitert: typische Symptome (amixer ùcannot find card 0ù, /dev/snd/ nur seq/timer, PipeWire nur Dummy Output), Ursache (fehlender Overlay vc4-kms-v3d-pi5), konkrete Schritte. In App-Dokumentation (Troubleshooting), INSTALL.md und PI_OPTIMIZATION.md ergùnzt.

---

## [1.2.0.4] ù 2026-02

### Pi-Optimierung & Erkennung

- **Pi-Erkennung:** Fallback ùber Device-Tree (`/proc/device-tree/model`) ù Raspberry Pi wird auch erkannt, wenn vcgencmd/cpuinfo fehlschlagen.
- **Raspberry Pi Config:** Menùpunkt erscheint nun zuverlùssig, sobald ein Pi erkannt wird.
- **CPU-Auslastung reduziert:** Light-Modus fùr Polling (`/api/system-info?light=1`); Dashboard-Polling auf dem Pi alle 30 s; Monitoring ohne Live-Polling auf dem Pi; Auslastung nur noch im Dashboard, nicht in Submenùs.
- **UI:** Card-Hover ohne Bewegung (nur Farbwechsel); StatCard-Icon ohne Animation; Hardware & Sensoren: Stats-Merge behùlt Sensoren/Laufwerke beim Polling.

### Dokumentation

- `PI_OPTIMIZATION.md`: Hinweise zu Pi-Erkennung, Raspberry Pi Config und abschaltbaren Services.

---

## [1.2.0.3] ù 2026-02

### Mixer-Installation

- **Backend:** Update und Install in zwei Schritten (`apt-get update`, dann `apt-get install`); Dpkg-Optionen `--force-confdef`/`--force-confold` fùr nicht-interaktive Installation; bei Fehler wird `copyable_command` zurùckgegeben; Timeout-Meldung klarer.
- **Frontend (Musikbox & Kino/Streaming):** Bei Fehler erscheint unter den Mixer-Buttons ein Hinweis ùInstallation fehlgeschlagen. Manuell im Terminal ausfùhren:ù mit Befehl und **Kopieren**-Button.

---

## [1.2.0.2] ù 2026-02

### Geùndert

- **Dashboard ù Hardware & Sensoren:** Bereich ùSysteminformationenù entfernt (ist bereits in der ùbersicht sichtbar).
- **CPU & Grafik:** Treiber-Hinweise (NVIDIA/AMD/Intel) werden nicht mehr unter der CPU angezeigt, sondern unter der jeweiligen Grafikkarte (iGPU bzw. diskret).

### Dokumentation

- In der Anzeige (Dokumentation ? Versionen & Changelog) nur die Endversion mit Details; ùltere Updates kompakt bzw. ùberspringbar.

---

## [1.2.0.1] ù 2026-02

### Behoben

- **Dashboard ù IP-Adressen:** Text unter den IPs (ùMit dieser IP von anderen Gerùten erreichbarùù) war anthrazit und bei Hover unleserlich ? jetzt `text-slate-200` und Link `text-sky-200`.
- **Dashboard ù Updates:** Zeile ùX Notwendig ù Y Optionalù war zu blass ? jetzt `text-slate-200` / `text-slate-100` fùr bessere Lesbarkeit.
- **Dashboard ù Menù:** Buttons ùùbersichtù, ùAuslastung & Grafikù, ùHardware & Sensorenù ù inaktive Buttons hatten fast gleiche Farbe wie Schrift ? jetzt `text-slate-200`, `bg-slate-700/70`, Hover `bg-slate-600`.
- **CPU & Grafik:** Es wurden 32 ùProzessorenù (Threads) gelistet ? ersetzt durch **eine** CPU-Zusammenfassung: Name, Kerne, Threads, Cache (L1ùL3), Befehlssùtze (aufklappbar), Chipsatz/Mainboard; integrierte Grafik und Grafikkarte unverùndert; Auslastung nur noch physikalische Kerne (keine Thread-Liste).
- **Mixer-Installation:** Installation schlug weiterhin fehl ? Sudo-Passwort wird getrimmt; `apt-get update -qq` vor install; `DEBIAN_FRONTEND=noninteractive` fùr update und install; Timeout 180s; Fehlermeldung bis 600 Zeichen; Logging bei Fehler.

### Backend

- `get_cpu_summary()`: Liest aus /proc/cpuinfo und lscpu Name, Kerne, Threads, Cache (L1ùL3), Befehlssùtze (flags).
- System-Info liefert `cpu_summary`; `hardware.cpus` wird auf einen Eintrag reduziert (keine Liste aller Threads).

---

## [1.2.0.0] ù 2026-02

### Neu

- **Musikbox fertig:** Musikbox-Bereich abgeschlossen ù Mixer-Buttons (pavucontrol/qpwgraph), Installation der Mixer-Programme per Knopfdruck (pavucontrol & qpwgraph), Sudo-Modal fùr Mixer-Installation.
- **Mixer:** Mixer in Musikbox und Kino/Streaming eingebaut ù ùMixer ùffnen (pavucontrol)ù / ùMixer ùffnen (qpwgraph)ù starten die GUI-Mixer; ùMixer-Programme installierenù installiert pavucontrol und qpwgraph per apt; Backend setzt `DISPLAY=:0` fùr GUI-Start; Installation mit `DEBIAN_FRONTEND=noninteractive` fùr robuste apt-Installation.
- **Dashboard:** Erweiterungen und Quick-Links; Versionsnummer und Changelog auf 1.2.0.0 aktualisiert.

### API

- `POST /api/system/run-mixer` ù Grafischen Mixer starten (Body: `{"app": "pavucontrol"}` oder `{"app": "qpwgraph"}`).
- `POST /api/system/install-mixer-packages` ù pavucontrol und qpwgraph installieren (Body optional: `{"sudo_password": "..."}`).

### Dokumentation

- Changelog 1.2.0.0 in App (Dokumentation ? Versionen & Changelog).
- Troubleshooting: Mixer-Installation fehlgeschlagen (manueller Befehl, Sudo, DISPLAY) in Dokumentation und INSTALL.md.
- INSTALL.md: API Mixer (run-mixer, install-mixer-packages); FEATURES.md: v1.2 Features; README Version 1.2.0.0.

---

## [1.0.4.0] ù 2026-01

- Sicherheit-Anzeige im Dashboard (2/5 aktiviert bei Firewall + Fail2Ban).
- Dokumentation & Changelog aktualisiert.

---

ùltere Eintrùge siehe **Dokumentation** in der App (Versionen & Changelog).
