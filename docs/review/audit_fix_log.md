# Audit Fix Log

## Datum
2026-03-09

## Bearbeitete Audit-Einträge (Priorität A)

| Audit-ID | Datei | Änderung | Risiko | Status |
|----------|------|----------|--------|--------|
| A-01 | `frontend/src/pages/DevelopmentEnv.tsx` | API-Aufruf `/api/devenv/configure` deaktiviert; Nutzer erhält klare Meldung „nicht verfügbar“ | gering | erledigt |
| A-01 | `frontend/src/pages/MailServerSetup.tsx` | API-Aufruf `/api/mail/configure` deaktiviert; Nutzer erhält klare Meldung „nicht verfügbar“ | gering | erledigt |
| A-02 | `backend/app.py` | Doppelte Route `POST /api/backup/verify` entfernt; erste Definition (Hauptpfad mit `results`) bleibt | mittel | erledigt |
| A-03 | `scripts/install-system.sh` | Konfigurationsdatei von `config.yaml` auf `config.json` umgestellt | mittel | erledigt |
| A-03 | `scripts/deploy-to-opt.sh` | Konfigurationsdatei von `config.yaml` auf `config.json` umgestellt | mittel | erledigt |
| A-03 | `docs/SYSTEM_INSTALLATION.md` | Doku-Pfad und Beispiel von `config.yaml` auf `config.json` aktualisiert | gering | erledigt |
| A-04 | `frontend/src-tauri/icons/` | Platzhalter-Icons (32x32, 128x128, 128x128@2x, icon.png, icon.ico) angelegt | gering | erledigt |
| A-04 | `frontend/public/docs/screenshots/` | Verzeichnis angelegt, README für spätere Screenshots ergänzt; UI zeigt weiterhin Platzhalter | gering | erledigt |

## Nicht automatisch lösbar
Keine.

## Priorität-B-Fixes

| Audit-ID | Datei | Änderung | Risiko | Status |
|----------|------|----------|--------|--------|
| B-01 | `backend/debug/debug.config.yaml` | Kommentar: PI_INSTALLER_DEBUG_CONFIG → PIINSTALLER_DEBUG_* | gering | erledigt |
| D-003 | `backend/core/eventbus.py` | `publish_fire_and_forget()` als zentraler Helper ergänzt | gering | erledigt |
| D-003 | `backend/services/pi_installer_service.py` | `_publish()` entfernt, nutzt `publish_fire_and_forget` | gering | erledigt |
| D-003 | `backend/services/sabrina_tuner_service.py` | `_publish()` entfernt, nutzt `publish_fire_and_forget` | gering | erledigt |
| D-002 | `scripts/archive/` | `.backup.*`-Skripte von scripts/ nach scripts/archive/ verschoben | gering | erledigt |
| B-02 | `QUICKSTART.md`, `backend/CONFIG.md`, `docs/REMOTE_COMPANION.md` | Port 3000→3001, CORS-Beispiele, Companion-Doku angepasst | gering | erledigt |
| D-004/B-05 | (Doku) | Sudo: SudoPasswordDialog (App.tsx), SudoPasswordModal (Setup-Seiten) – Nutzung dokumentiert | - | dokumentiert |

---

## Abschlussbericht Priorität-B-Fixes

**Datum:** 2026-03-09

### Statistik

| Kategorie | Anzahl |
|-----------|--------|
| Behobene Dubletten | 2 (D-003 `_publish()`, D-002 Backup-Skripte) |
| Entfernter Copy-Paste-Code | 1 (D-003: gemeinsamer `publish_fire_and_forget`) |
| Vereinfachte Strukturen | 1 (B-01 Debug-Konfig-Kommentar) |
| Doku-Konsolidierung | 3 (B-02 Ports, D-004/B-05 Sudo, B-01 ENV) |

### Verbleibende Priorität-B-Probleme

- **B-03:** Logpfad-Konzept (`pi-installer` vs. `piinstaller`) – nicht angefasst
- **B-04:** Alte Parallelarchitekturen `backend/modules/*` vs. `app.py` – nicht angefasst

### Die 10 wichtigsten strukturellen Verbesserungen

1. **D-003:** Zentraler Eventbus-Helper `publish_fire_and_forget()` – beide Services nutzen ihn
2. **D-002:** Backup-Skripte nach `scripts/archive/` ausgelagert – aktiver Script-Bereich aufgeräumt
3. **B-01:** Debug-Konfig-Kommentar auf PIINSTALLER_DEBUG_* vereinheitlicht
4. **B-02:** Port-Standard 3001/8000 in QUICKSTART, CONFIG, REMOTE_COMPANION konsolidiert
5. **D-004/B-05:** Sudo-Komponenten in `docs/development/SUDO_COMPONENTS.md` dokumentiert
6. Unnötige `asyncio`-Imports in beiden Services entfernt
7. CORS-Doku auf Frontend-Port 3001 umgestellt
8. Companion-Doku: PWA-Zugriff über 3001 (Frontend), API über 8000 geklärt
9. Code-Marker AUDIT-FIXED in Debug-Config und Sudo-Komponenten ergänzt
10. Fix-Log-Tabelle für Priorität B ergänzt

---

## Phase-4-Strukturänderungen

| ID | Datei/Bereich | Änderung | Risiko | Status |
|----|---------------|----------|--------|--------|
| P4-01 | docs/architecture/config_flow.md | Neu: Konfigurationsfluss dokumentiert | keins | erledigt |
| P4-02 | docs/architecture/debug_flow.md | Neu: Debugfluss dokumentiert | keins | erledigt |
| P4-03 | docs/architecture/init_flow.md | Neu: Start-/Initialisierungsfluss dokumentiert | keins | erledigt |
| P4-04 | docs/architecture/foundation_vs_advanced_map.md | Neu: Grundlagen/Erweitert-Kandidaten kartiert | keins | erledigt |
| P4-05 | backend/modules/README.md | Neu: Modulverantwortlichkeiten, aktiv vs. ungenutzt | keins | erledigt |
| P4-06 | docs/review/phase4_structural_simplification.md | Neu: Phase-4-Dokumentation | keins | erledigt |

---

## Phase-5-UI-Modus-Trennung

| ID | Datei/Bereich | Änderung | Risiko | Status |
|----|---------------|----------|--------|--------|
| P5-01 | frontend/src/context/UIModeContext.tsx | Neu: UIMode (basic/advanced/diagnose), persistiert in localStorage | gering | erledigt |
| P5-02 | frontend/src/components/Sidebar.tsx | Modus-Tabs, Menüfilter nach Modus, MENU_MODE pro Seite | gering | erledigt |
| P5-03 | frontend/src/App.tsx | UIModeProvider um Wurzel | gering | erledigt |
| P5-04 | frontend/src/pages/ControlCenter.tsx | Toggle „Erweiterte Optionen“ (Performance, Lüfter, RGB) | gering | erledigt |
| P5-05 | docs/architecture/ui_modes.md | Neu: Klassifizierung Grundlagen/Erweitert/Diagnose | keins | erledigt |

---

## Phase-6-UX-Optimierung

| ID | Datei/Bereich | Änderung | Risiko | Status |
|----|---------------|----------|--------|--------|
| P6-01 | docs/architecture/ux_guidelines.md | Neu: UX-Prinzipien, Begriffe, Fehlerstruktur | keins | erledigt |
| P6-02 | frontend/src/pages/Dashboard.tsx | Status + Fehlermeldung verständlicher formuliert | gering | erledigt |
| P6-03 | frontend/src/components/SudoPasswordDialog.tsx | Server-Meldung + Toast verbessert | gering | erledigt |
| P6-04 | frontend/src/pages/UserManagement.tsx | Speichern-Fehler verständlicher | gering | erledigt |
| P6-05 | frontend/src/pages/SettingsPage.tsx | Backend→Server, Verbindung-Bereich klarer | gering | erledigt |
| P6-06 | frontend/src/pages/ControlCenter.tsx | Toast-Fallback „Server nicht erreichbar“ | gering | erledigt |
| P6-07 | frontend/src/App.tsx | Tooltip Server bereit / Server nicht erreichbar | gering | erledigt |
| P6-08 | docs/review/phase6_ux_report.md | Abschlussbericht Phase 6 | keins | erledigt |

---

## Manuell zu prüfende Stellen
- Bestehende Installationen mit `config.yaml` in `/etc/pi-installer/`: Diese werden vom Backend weiterhin nicht gelesen. Migration auf `config.json` ggf. manuell vornehmen oder Skript bereitstellen.
- Tauri-Icons: Aktuell graue Platzhalter; für Produktionsrelease eigene App-Icons erwünscht.
- Screenshots: Verzeichnis existiert; tatsächliche Screenshot-Dateien können bei Bedarf ergänzt werden.
