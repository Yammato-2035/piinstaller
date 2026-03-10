# System Audit Report

_Stand: 2026-03-09_

Hinweis: Dieser Report dokumentiert einen kontrollierten Audit-Schritt. Es wurden keine funktionalen Bereinigungen vorgenommen. Das Fremdprojekt `ckb-next` wurde nur dort berücksichtigt, wo es das Hauptrepo direkt beeinflusst (Submodul-/Strukturfragen), nicht als First-Party-Codebasis.

## 1. Zusammenfassung

Kurzüberblick:
- Das Projekt ist funktional breit gewachsen: monolithisches Backend, React-/Tauri-Frontend, viele Installations- und Hardwareskripte, neue Remote-/Debug-Strukturen und umfangreiche Dokumentation.
- Die größten Altlasten entstehen nicht primär durch einzelne Bugs, sondern durch parallel gewachsene Wahrheiten: alte und neue Endpunkte, mehrere Konfigurationsquellen, alte und neue Debug-Welten sowie mehrfach vorhandene Script-/Service-Pfade.
- Besonders kritisch sind Stellen, an denen UI bereits aktive Pfade anbietet, deren Backend-Ziel nicht oder nicht mehr existiert.

Gefundene Problemstellen pro Kategorie:

| Kategorie | Anzahl | Einordnung |
|---|---:|---|
| Tote / veraltete Links und Verweise | 8 | 6 bestätigt, 1 wahrscheinlich, 1 unklar |
| Doppelte Funktionen / doppelte Logik | 6 | 4 bestätigt, 2 wahrscheinlich |
| Doppelte / widersprüchliche Konfigurationen | 10 | 8 bestätigt, 2 wahrscheinlich |
| Alte Debugging-Reste / Performance-Risiken | 9 | 5 bestätigt, 3 wahrscheinlich, 1 unklar |
| Vereinfachungspotenzial im Code | 7 | 2 bestätigt, 5 wahrscheinlich |
| Grundlagen / Erweitert-Kandidaten | 5 | 5 wahrscheinlich |

Größte Risiken:
- `ROT`: Frontend-Aktionen verweisen auf nicht implementierte Backend-Endpunkte.
- `ROT`: dieselbe Backup-Route ist doppelt definiert.
- `ORANGE`: konkurrierende Konfigurationsquellen (`config.yaml` vs. `config.json`, alte vs. neue ENV-/Debug-Pfade).
- `ORANGE`: neue Debug-Infrastruktur existiert, ist aber nur teilweise angebunden; parallel läuft altes Logging weiter.
- `ORANGE`: Tauri-Bundle referenziert Icons, die im Repo-Stand fehlen.

Größte Vereinfachungspotenziale:
- Monolithisches `backend/app.py` vs. parallele Modularchitektur.
- Viele ähnliche Setup-Seiten mit wiederholter UI-/Fetch-/Sudo-Logik.
- Mehrere nahezu gleichartige Audio-/Display-/Fix-Skripte.
- Doku-Doppelpflege zwischen `Documentation.tsx` und Markdown-Dateien.

Farbkategorien für spätere Abarbeitung:
- `ROT` = akuter Fehler / hohes Risiko
- `ORANGE` = wahrscheinlich problematisch
- `GELB` = prüfen / unklar
- `BLAU` = strukturelle Vereinfachung
- `GRÜN` = bereits sauber / unkritisch

## 2. Tote / veraltete Links und Verweise

| ID | Datei / Modul | Typ | Fundstelle | Beschreibung | Status | Risiko | Empfehlung für späteren Fix |
|---|---|---|---|---|---|---|---|
| L-001 | `frontend/src/pages/DevelopmentEnv.tsx` | API | `fetchApi('/api/devenv/configure')` | Frontend ruft aktiven Endpunkt auf, im Backend ist dafür nur ein TODO-Hinweis vorhanden. | tot | ROT | Endpunkt implementieren oder UI-Aktion bis zur Umsetzung klar als nicht verfügbar markieren. |
| L-002 | `frontend/src/pages/MailServerSetup.tsx` | API | `fetchApi('/api/mail/configure')` | Gleiches Muster wie bei Development Environment: UI-Pfad vorhanden, Backend-Ziel fehlt. | tot | ROT | Endpunkt implementieren oder Button/Flow später entkoppeln. |
| L-003 | `frontend/src/pages/Documentation.tsx`, `README.md`, `INSTALL.md`, `QUICKSTART.md` | Asset / Doku | `docs/screenshots/*.png` | Screenshots werden referenziert, im Repo existiert aber kein `docs/screenshots/`-Ordner. | tot | ORANGE | Asset-Quelle festziehen oder Referenzen auf echten Speicherort umstellen. |
| L-004 | `frontend/src-tauri/tauri.conf.json` | Asset / Packaging | `bundle.icon` | Mehrere Tauri-Icons sind referenziert, der Ordner `frontend/src-tauri/icons/` fehlt im Repo-Stand. | tot | ROT | Build-Assets nachziehen oder Bundling-Konfiguration konsolidieren. |
| L-005 | `frontend/src/pages/Documentation.tsx` | URL | externer Arch-Linux-Doku-Link | Der dokumentierte Link `https://www.archlinux.org/docs/` liefert nicht mehr die erwartete Seite. | veraltet | GELB | Auf gültige Zielseite aktualisieren oder entfernen. |
| L-006 | `docs/REMOTE_COMPANION.md` | Doku / Portpfad | Companion-URL `http://<pi-ip>:8000` | Doku beschreibt Zugriff über Backend-Port, während das Frontend an anderer Stelle auf `3001` bzw. Tauri verweist. | veraltet | ORANGE | Eine klare Source of Truth für Companion-Zugriff festlegen und Doku angleichen. |
| L-007 | `frontend/src/pages/HomeAutomationSetup.tsx`, `MusicBoxSetup.tsx`, `MonitoringDashboard.tsx`, `DevelopmentEnv.tsx` | Navigation / Deep Link | diverse `http://localhost:*` Links | Für Remote-Nutzung zeigen diese Links auf den falschen Rechner; lokal kann es korrekt sein. | wahrscheinlich veraltet | ORANGE | Für spätere Prüfung zwischen lokalem Admin-Modus und Remote-Client unterscheiden. |
| L-008 | `README.md`, `docs/GET_PI_INSTALLER_IO.md`, `scripts/create_installer.sh` | Download / URL | `https://get.pi-installer.io` | Domain reagierte während des Audits mit `503`; unklar, ob temporär oder dauerhaft. | unklar | GELB | Manuell live verifizieren; bei Bedarf Doku und Bootstrap-Pfad korrigieren. |

## 3. Doppelte Funktionen / doppelte Logik

| ID | Datei 1 / Funktion 1 | Datei 2 / Funktion 2 | Art der Dublette | Beschreibung | Vermuteter Hauptpfad | Risiko | Empfehlung für späteren Fix |
|---|---|---|---|---|---|---|---|
| D-001 | `backend/app.py` / `verify_backup()` | `backend/app.py` / `verify_backup()` | echte Dublette | Dieselbe Route `POST /api/backup/verify` ist zweimal definiert. | unklar | ROT | Einen Hauptpfad festlegen und die zweite Definition fachlich einordnen. |
| D-002 | `scripts/apply-dual-display-x11-delayed.sh` | `scripts/apply-dual-display-x11-delayed.sh.backup.*` | Altversion | Mehrere nahezu identische Backup-Skripte liegen im aktiven Script-Verzeichnis. | `apply-dual-display-x11-delayed.sh` | ORANGE | Backup-Artefakte später auslagern oder dokumentiert archivieren. |
| D-003 | `backend/services/pi_installer_service.py` / `_publish()` | `backend/services/sabrina_tuner_service.py` / `_publish()` | fast identische Parallelimplementierung | Eventbus-Helper ist praktisch wortgleich doppelt vorhanden. | keiner klar bevorzugt | BLAU | Gemeinsamen Helper später zentralisieren. |
| D-004 | `frontend/src/components/SudoPasswordDialog.tsx` | `frontend/src/components/SudoPasswordModal.tsx` | fast identische Parallelimplementierung | Zwei Sudo-Dialogkomponenten mit überlappendem Zweck und ähnlicher UX-Verantwortung. | `SudoPasswordModal.tsx` wirkt aktiver | ORANGE | Nutzungspfad je Komponente dokumentieren und später vereinheitlichen. |
| D-005 | `backend/modules/security.py`, `webserver.py`, `devenv.py`, `mail.py` | `backend/app.py` | Altversion neben neuer Implementierung | Fachlogik scheint teils in Modulen, teils direkt im Monolithen zu leben. | `backend/app.py` | ORANGE | Für jeden Bereich Source of Truth definieren, bevor etwas entfernt wird. |
| D-006 | `backend/modules/backup.py` | `backend/app.py` Backup-/Restore-Logik | Altversion / Parallelarchitektur | Backup-Logik wirkt halb migriert; das Modul erwartet Abhängigkeiten, die der Aufrufer nicht injiziert. | `backend/app.py` | ORANGE | Backup-Pfad später architektonisch konsolidieren. |

## 4. Doppelte / widersprüchliche Konfigurationen

| ID | Datei / Bereich | Schlüssel / Setting / Parameter | Problemtyp | Beschreibung | Auswirkung | Risiko | Empfehlung für späteren Fix |
|---|---|---|---|---|---|---|---|
| C-001 | `scripts/install-system.sh`, `debian/postinst`, `backend/app.py` | `config.yaml` vs. `config.json` | konkurrierende Konfigurationsquellen | Installation und Doku schreiben YAML, Laufzeit liest JSON. | Systemweite Konfiguration kann wirkungslos bleiben. | ROT | Primäre Runtime-Konfigurationsquelle festlegen und Doku angleichen. |
| C-002 | `scripts/install-system.sh`, `debian/pi-installer.service`, `backend/app.py` | `PI_INSTALLER_DIR`, `PI_INSTALLER_CONFIG_DIR`, `PI_INSTALLER_LOG_DIR` | redundante / ungenutzte Initialisierung | Installer exportiert Pfade, Backend verwendet sie aber nicht konsistent. | Installierte Pfade und tatsächliche Laufzeitpfade driften auseinander. | ORANGE | ENV-Source of Truth später definieren. |
| C-003 | `backend/debug/debug.config.yaml`, `backend/debug/config.py` | `PI_INSTALLER_DEBUG_CONFIG` vs. `PIINSTALLER_DEBUG_*` | widersprüchliche Doku / Runtime | Kommentar in YAML nennt Quellen, die der Loader nicht unterstützt. | Fehlkonfiguration und falsche Erwartung an Debug-Steuerung. | ORANGE | Kommentar und Loader später harmonisieren. |
| C-004 | `backend/CONFIG.md`, `backend/app.py` | `.env` / `SERVER_HOST`, `CORS_ORIGINS`, `SECRET_KEY` etc. | dokumentierte, aber nicht verdrahtete Konfiguration | `.env`-Mechanik wird beschrieben, im Runtime-Code aber nicht sichtbar geladen. | Dokumentation erzeugt trügerische Konfigurationssicherheit. | ORANGE | Dokumentierte ENV nur behalten, wenn sie tatsächlich gelesen werden. |
| C-005 | `docker-compose.yml`, `frontend/src/api.ts`, `frontend/vite.config.ts`, `nginx.conf` | `VITE_API_URL`, `VITE_API_BASE`, `VITE_PROXY_TARGET` | widersprüchliche Defaults | Container-/Proxy-Setup nutzt andere Schlüssel und Ports als das Frontend. | Reverse-Proxy- und Containerbetrieb werden fehleranfällig. | ORANGE | Frontend-API-Ziel konsolidieren. |
| C-006 | `apps/dsi_radio/dsi_radio.py`, `apps/dsi_radio/dsi_radio_qml.py`, `backend/app.py` | DSI-Radio-Konfigpfad | konkurrierende Pfadlogik | App nutzt `XDG_CONFIG_HOME`, Backend arbeitet mit hartem `~/.config/pi-installer-dsi-radio`. | Backend und App können an unterschiedlichen Orten lesen/schreiben. | ORANGE | Konfigurationspfad für Radio eindeutig festziehen. |
| C-007 | `start-backend.sh`, `start-pi-installer.sh`, `start-frontend-desktop.sh`, `frontend/src-tauri/tauri.conf.json` | Backend-Port `8000` / `PI_INSTALLER_BACKEND_PORT` | teilweise konfigurierbar | Nur einzelne Startpfade respektieren den variablen Port. | Nebenpfade und Doku laufen bei Portabweichung ins Leere. | ORANGE | Portquelle später zentralisieren. |
| C-008 | `frontend/vite.config.ts`, `docs/START_APPS.md`, `backend/CONFIG.md`, `QUICKSTART.md` u. a. | Frontend-Port `3000` vs. `3001` | widersprüchliche Defaults | Alte Portannahmen stehen neben aktuellem Port `3001`. | Falsche Doku, falsche CORS-/Proxy- und Startannahmen. | ORANGE | Einen aktuellen Standardport festschreiben und alle Texte anpassen. |
| C-009 | `backend/app.py`, `backend/debug/paths.py`, `backend/debug/support_bundle.py`, `scripts/install-system.sh` | Log-Pfade mit / ohne Bindestrich | inkonsistente Pfadnamen | `pi-installer`, `piinstaller` und repo-lokale `logs/` koexistieren. | Logs landen je nach Pfadwelt an unterschiedlichen Orten. | ORANGE | Log-Pfadkonzept dokumentieren und später vereinheitlichen. |
| C-010 | `pi-installer.service`, `pi-installer.service.install`, `debian/pi-installer.service`, `pi-installer-backend.service` | Service-Templates | divergierende Konfigurationsquellen | Mehrere Service-Definitionen mit unterschiedlicher Semantik und Zuständigkeit. | Unterschiedliches Verhalten je Installationsweg. | wahrscheinlich widersprüchlich | ORANGE | Aktives Service-Modell später klar festlegen. |

## 5. Alte Debugging-Reste / Performance-Risiken

| ID | Datei / Modul | Debug-Typ | Fundstelle | Mögliche Auswirkung auf Performance / Lesbarkeit / Wartung | Status im Verhältnis zum neuen Debuggingsystem | Empfehlung für späteren Fix |
|---|---|---|---|---|---|---|
| G-001 | `backend/app.py` | paralleles Alt-Logging | klassischer File-/Console-Logger, `/api/logs/path`, `/api/logs/tail` | Zwei Logging-Welten erhöhen Pflegeaufwand und erschweren Support. | vorhanden, aber parallel statt ersetzt | Alte und neue Log-Welt fachlich gegeneinander abgrenzen. |
| G-002 | `backend/debug/support_bundle.py` | möglicher Laufzeitfehler | `_redact_text_line_by_line()` nutzt `compile_patterns()` ohne sichtbaren Import | Support-Bundle-/Redaction-Pfad kann erst im Problemfall scheitern. | Teil des neuen Systems, aber unklar robust | Laufzeitpfad manuell testen und Import-/Abhängigkeitslage später bereinigen. |
| G-003 | `backend/debug/logger.py` | I/O-intensives Logging | Event-Write mit `flush()` und `os.fsync()` | Unter hohem Debug-Aufkommen potenziell spürbare I/O-Bremse. | neues System | Performancegrenzen später messen und ggf. Pufferstrategie prüfen. |
| G-004 | `backend/debug/support_bundle.py` | speicherintensive Logsammlung | Debug-Logs werden erst gesammelt, dann gekürzt | Unnötiger RAM-Verbrauch bei großen Logdateien. | neues System | Streaming-/Tail-Strategie später prüfen. |
| G-005 | `frontend/src/pages/SecuritySetup.tsx` | `console.*`-Dauerfeuer | viele Debug-Ausgaben | Rauschen in Devtools, schwerer Support, potentiell sensible Daten in Browser-Konsole. | nicht ans neue System angebunden | Konsolen-Debug später zentralisieren oder entkoppeln. |
| G-006 | `frontend/src/pages/BackupRestore.tsx` | `console.*`-Dauerfeuer | Cloud-/Polling-Debug | Browser-Logs und Datenpfade werden unruhig und uneinheitlich. | nicht ans neue System angebunden | Später durch gezielte Debug-Hooks oder Backend-Korrelation ersetzen. |
| G-007 | `backend/oled_display_runner.py`, `backend/app.py` | direkte `print()`-Reste | Runner-/Backup-nahe Codepfade | Zusätzliche, unstrukturierte Laufzeitausgaben. | alte Welt | Nur nach Nutzungsanalyse in strukturiertes Logging überführen. |
| G-008 | `scripts/diagnose-*.sh`, `scripts/test-*.sh` | Shell-Diagnosepfade | Echo-/journalctl-/dmesg-lastig | Diagnosewelt ist nicht zentral steuerbar und schwer korrelierbar. | außerhalb des neuen Systems | Erst Nutzungshäufigkeit dokumentieren, dann eventuell vereinheitlichen. |
| G-009 | `frontend/src/pages/SettingsPage.tsx` | UI-Lücke | Logs-Tab zeigt nur klassische Backend-Logs | Neues JSONL-Debugsystem ist in der UI nicht sichtbar oder steuerbar. | teilweise vorhanden, nicht UI-sichtbar | Später klar dokumentieren, welche Logs Benutzer wo sehen sollen. |

## 6. Abdeckung des neuen Debuggingsystems

| Modulname / Bereich | Debugging vorhanden | UI-Sichtbarkeit | zentrale Steuerbarkeit | Logging vorhanden | offene Lücken | Bemerkung |
|---|---|---|---|---|---|---|
| Backend-Kern (`backend/debug`, Teile von `backend/app.py`) | ja | ja, aber indirekt | ja, über Datei/ENV | ja | Parallelbetrieb mit altem Logger | Neue Infrastruktur ist real vorhanden, aber nicht alleinige Wahrheit. |
| Frontend/UI | teilweise | ja | nein | teilweise | primär `console.*`, keine zentrale Korrelation | Kein klarer Frontend-Debugkanal auf Niveau des Backends. |
| Installer-/Setup-Strecken (`scripts/`, Setup-Seiten) | teilweise | ja | nein | teilweise | viele Shell- und UI-Sonderpfade | Stark historisch gewachsen. |
| Konfigurations-/Persistenzlogik | teilweise | nein | teilweise | teilweise | `.env`-/Datei-/Pfadquellen unscharf | Debug- und Konfigurationssystem greifen nicht sauber ineinander. |
| Geräte-/Netzwerk-/Hardwaremodule | teilweise | ja | teilweise | teilweise | punktuelle Instrumentierung, viele Ausnahmen | Neue Instrumentierung sichtbar, aber nur in Teilbereichen. |
| Fehlerdialoge / Statusanzeigen / Support | teilweise | ja | nein | teilweise | Support-Bundle nicht sichtbar, Logpfade uneinheitlich | Bedienlogik und Debugdaten sind nur lose verbunden. |

## 7. Vereinfachungspotenzial im Code

| ID | Datei / Modul | Kategorie | Beschreibung | Warum unnötig komplex | Geschätzter Nutzen einer späteren Vereinfachung | Risiko bei Änderung | Empfehlung |
|---|---|---|---|---|---|---|---|
| S-001 | `backend/app.py` | Zuständigkeiten | Monolith vereint API, Systemlogik, Prozessaufrufe, Backup, Settings und Diagnose. | Viele fachliche Verantwortungen an einem Ort. | sehr hoch | hoch | Erst fachliche Source of Truth je Bereich dokumentieren. |
| S-002 | `frontend/src/pages/*Setup*.tsx` | Copy-Paste-UI | Mehrere Setup-Seiten wiederholen Karten, Statusladen, Konfig-POST und Sudo-Flows. | Gleiche UX-/Fetch-Muster werden lokal neu gebaut. | hoch | mittel | Gemeinsame UI-Bausteine später ableiten. |
| S-003 | `frontend/src/pages/Documentation.tsx` + `docs/*.md` | Doku-Doppelpflege | Handbuch lebt als große TSX-Datei neben vielen Markdown-Dokumenten. | Inhaltliche Pflege verteilt sich über zwei Dokuwelten. | mittel bis hoch | mittel | Künftige Doku-Quelle vereinheitlichen. |
| S-004 | `scripts/` Freenove/HDMI/Audio | Script-Landschaft | Viele ähnliche Diagnose-/Fix-/Test-Skripte für eng verwandte Probleme. | Hohe kognitive Last und unklare Zuständigkeit. | hoch | mittel | Später in Diagnose/Aktivieren/Fix gruppieren, aber erst nach Nutzungsanalyse. |
| S-005 | `backend/services/*` | Helper-Duplizierung | Wiederholte Eventbus-Helfer und Stub-Strukturen. | Kleine Wiederholungen streuen Technikschuld. | mittel | niedrig | Später gemeinsame Hilfsfunktionen extrahieren. |
| S-006 | `frontend/src/App.tsx` | Produktgrenzen | Installer, Remote Companion, DSI-Radio und Sonderpfade teilen sich eine große Navigation. | Verschiedene Nutzungskontexte werden gleich behandelt. | mittel bis hoch | mittel | Später Informationsarchitektur nach Nutzungsszenario prüfen. |
| S-007 | `pi-installer.service*`, `pi-installer-backend.service`, `debian/*` | Deployment-Modell | Mehrere Service- und Packaging-Pfade beschreiben ähnliche Startaufgaben unterschiedlich. | Erhöht Wartungs- und Testaufwand. | hoch | hoch | Erst aktiven Installationspfad festziehen, dann vereinfachen. |

## 8. Mögliche Trennung in Grundlagen / Erweiterte Funktionen

| ID | Bereich / Screen / Modul | Derzeitige Komplexität | Was in “Grundlagen” gehören würde | Was in “Erweitert” gehören würde | Nutzen für Anwender | Risiko / Abhängigkeit | Empfehlung |
|---|---|---|---|---|---|---|---|
| U-001 | `frontend/src/pages/ControlCenter.tsx` | sehr hoch | WLAN, SSH, VNC, Sprache, Tastatur, Standard-Display | Performance, ASUS-ROG-Lüfter, Corsair/RGB, Telemetrie | Weniger Überforderung im Alltagsbetrieb | mittel | Sehr guter Kandidat für spätere Trennung. |
| U-002 | `frontend/src/pages/RaspberryPiConfig.tsx` + `backend/modules/raspberry_pi_config.py` | sehr hoch | Anzeige, Standard-Audio, typische Peripherie | Overclocking, EDID, Overlays, UART/GPIO/Kamera | Weniger Fehlbedienungen bei Low-Level-Optionen | hoch | Nur nach fachlicher Risikoanalyse anfassen. |
| U-003 | `frontend/src/pages/BackupRestore.tsx` | hoch | lokales Sichern/Wiederherstellen | Cloud, Verschlüsselung, Zeitpläne, USB-Formatierung, Disk-Klonen | Basis-Backup wird zugänglicher | hoch | Kritischer Pfad, nur nach Konzepttrennung angehen. |
| U-004 | `frontend/src/App.tsx` / Hauptnavigation | hoch | Installer / Standardverwaltung | Remote, Radio/TFT-Apps, Spezialfunktionen | Klarere Produktgrenzen | mittel | Gute strategische Maßnahme, aber nicht kurzfristig. |
| U-005 | `frontend/src/pages/Documentation.tsx` | mittel bis hoch | Erste Schritte, Standard-Setups, häufige Aufgaben | Freenove, DSI, Remote, Spezialhardware | Einsteiger finden schneller relevante Hilfe | niedrig bis mittel | Schnell guter UX-Nutzen, sofern Doku-Quelle geklärt wird. |

## 9. Priorisierte Maßnahmenliste für den NÄCHSTEN Schritt

Priorität A = hohes Risiko / klare Fehlerquelle
- A-01: UI-Endpunkte `POST /api/devenv/configure` und `POST /api/mail/configure` gegen reale Backend-Implementierung oder klare Nichtverfügbarkeit abgleichen.
- A-02: Doppelte Route `POST /api/backup/verify` fachlich auflösen und Hauptpfad festlegen.
- A-03: Konfigurations-Source-of-Truth für Haupt-App festlegen: `config.yaml` vs. `config.json`.
- A-04: Fehlende Tauri-Icons und fehlende `docs/screenshots/*`-Assets gegen Build- und Doku-Realität prüfen.

Priorität B = mittleres Risiko / hohe Wartungslast
- B-01: Debug-Konfiguration und Dokumentation (`PI_INSTALLER_DEBUG_CONFIG` vs. `PIINSTALLER_DEBUG_*`) harmonisieren.
- B-02: Port- und API-Zielannahmen (`3000`/`3001`, `8000`, Companion-Doku, `localhost`-Links) konsolidieren.
- B-03: Logpfad-Konzept vereinheitlichen (`pi-installer` vs. `piinstaller`, altes vs. neues Logging).
- B-04: Alte Parallelarchitekturen in `backend/modules/*` gegenüber `backend/app.py` katalogisieren.
- B-05: Sudo-Komponenten und wiederholte Setup-UI-Flows auf einen klaren Hauptpfad abbilden.

Priorität C = kosmetisch / strukturell / später
- C-01: Doku-Doppelpflege zwischen `Documentation.tsx` und Markdown reduzieren.
- C-02: Eingecheckte `.backup.*`-Skripte aus aktivem Arbeitsbereich auslagern oder dokumentiert archivieren.
- C-03: Grundlagen/Erweitert-Kandidaten fachlich priorisieren, ohne sofort UI umzubauen.
