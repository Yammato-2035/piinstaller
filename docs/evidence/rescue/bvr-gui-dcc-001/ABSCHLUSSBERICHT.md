# PI-RS-BVR-GUI-DCC-001 – Abschlussbericht

**Endstatus: `passed_with_gui_fallback`**

Datum: 2026-07-22 · Feature-Branch tip (vor diesem Evidence-Commit): `71717ec5` · Baseline: `6d90ab3e`

---

## 1. Workspace

- Pfad: `/home/volker/piinstaller`
- Git-Root: `/home/volker/piinstaller`
- Repository: `piinstaller` (`origin` → `Yammato-2035/piinstaller`)
- Workspace-Wechsel: nein
- falscher Workspace ausgeschlossen: ja

## 2. Git

- Ausgangsbranch: `pi-rs-e2e-live-001d-physical-backup-restore` @ `6d90ab3e`
- Feature-Branch: `pi-rs-bvr-gui-dcc-001-http-i18n-drift-deploy`
- HEAD vorher: `6d90ab3e`
- HEAD Implementierung: `4098f004` (Deploy-/USB-Quelle) … Evidence-Commits folgen
- origin/main: `b8651d33` (Feature-Abstand dokumentiert als yellow, nicht auto-rot)
- Baseline-Commit `6d90ab3e` enthalten: ja
- Commits (Feature):
  1. `43d5da91` Fix rescue GUI HTTP runtime
  2. `f0065d0b` Stick i18n + Payload 1.10.1.1
  3. `bc94bccd` DCC BVR/GUI + Drift-Contract
  4. `4098f004` FAQ/KB/Status
  5. `0f6c22c3` USB inject + /opt deploy Evidence
  6. `71717ec5` Drift-Matrix nach Deploy
  7. (dieser Abschluss) physische Retest-Evidence + Bericht
- Push: Feature-Branch auf `origin` (bereits zuvor gepusht; Evidence nachziehen)
- fremde Drift: vorhanden, **unangetastet** (u. a. Asus/Pi5, lokale `config/version.json` 1.9.20.2 dirty)
- unerwartete Drift: keine der Feature-Arbeit zugeordnet

## 3. Ausgangslauf

- Run-ID: `e2e-rescue-msi-20260721-232222-ba58c7a7`
- Payload: `1.10.1.0`
- Backup / Verify / Restore / Manifest: passed
- GUI: nein (`http_server_failed`)
- Fallback: ja
- Gesamtstatus: `passed_with_gui_fallback`

## 4. Root Cause (Baseline-GUI)

- primäre Ursache: Non-ASCII in Python-`b'...'`-Literal (Ellipsis) → `SyntaxError` → HTTP-Server tot
- sekundäre Ursachen: irreführende `msi_compat_nomodeset`-Statusdateien (blockierten diesen GUI-Boot nicht)
- betroffene Dateien: inline-Server in `setuphelfer-rescue-ui-launch` (ersetzt)
- Exitcode: 1
- Port: 8765 · Document Root: `/usr/share/setuphelfer/rescue/ui`
- Berechtigungen: ok · Startreihenfolge: Server crash vor Chromium
- Payload-Drift (Baseline): nein
- Confidence: **high**

## 5. GUI-/HTTP-Fix

- Server: `scripts/rescue-live/image/setuphelfer-rescue-ui-http-server` (ASCII-safe)
- Bind: `127.0.0.1` · Port: `8765`
- Readiness: `/health.json` vor Chromium
- Asset-/i18n-Preflight: ja (4 Locales für Progress-Seite)
- Chromium-Handoff: erst nach ready
- Watchdog: **beibehalten**
- Fehlercodes: `rescue.gui.*`
- BVR-Core verändert: **nein**

### Physischer Retest (GUI-Schicht)

- HTTP auf MSI: **ready** (verifiziert in Evidence)
- Chromium für Operator: **nicht sichtbar**
- Watchdog: `openvt_console_2_not_released` → TUI-Fallback
- zusätzlicher Fallback-Code in Evidence: `msi_compat_nomodeset`

## 6. i18n

- de-DE / en-US / fr-FR / nl-NL: Dateien vorhanden, Key-Parität (11 Keys)
- fehlende Keys vorher: keine Locale-Dateien für Progress-UI
- fehlende Keys nachher: keine
- rohe Keys: in Unit-/Locale-Gate nicht beobachtet
- TUI/GUI Locale-Contract: GUI-Locales + Health-Locale; TUI-Progress separat (Anzeige-Bug, siehe unten)
- Payload-Prüfung: Locales im Squash vorhanden
- Encoding: UTF-8 JSON / ASCII-safe Server-Responses

## 7. DCC

- BVR-Kern-Anzeige: Modell trennt BVR grün / GUI gelb bei Fallback
- Baseline/Retest: `passed_with_gui_fallback` (kein Fake-Green)
- DCC-API unter `/opt`: Profil `release` blockiert Developer-Routen (`DEVELOPER_CAPABILITY_REQUIRED`)
- Module unter `/opt` deployed: `rescue_bvr_dcc_status.py`, `version_commit_drift.py`
- nächster Schritt (DCC): Developer-Capability/Profil für Status-Endpoint freigeben

## 8. Version und Drift

| Komponente | Version | Commit | SHA256 | Status |
|---|---|---|---|---|
| Workspace (Feature tip SoT) | project `1.9.20.0` / payload `1.10.1.1` | Feature-Commits | — | green (committed) |
| /opt-Runtime | `1.9.20.0` | Deploy-Quelle `4098f004` | — | green (nach Deploy) |
| Backend API | `1.9.20.0` | — | — | green |
| Frontend (Deploy-Build) | Semver-Projektion `1.9.20` | — | — | green |
| Payload | `1.10.1.1` | `4098f004` | `2c0a1552…22fbbb2` | green |
| USB-Stick | `1.10.1.1` | `4098f004` | `2c0a1552…22fbbb2` | green |

- finaler Driftstatus (Feature-Identitäten): **yellow** (origin/main Abstand; DCC-Profil-Warnung; dirty fremde Workspace-Dateien)
- verbleibende Warnungen: DCC release-Profil; fremde uncommitted Drift im Workspace

## 9. Deploy nach /opt

- Deploy-Methode: `scripts/deploy-to-opt.sh` aus clean worktree
- Commit: `4098f004`
- Runtime vorher: `1.9.20.2` (älterer Dirty-Stand)
- Runtime nachher: `1.9.20.0` @ `/opt/setuphelfer/backend`
- Services: `setuphelfer-backend` active
- `/api/version`: HTTP 200
- Runtime-Gate: DCC-404 im release-Profil erwartet
- Deploy-Drift: `deployed_with_warning`
- manueller Workaround verblieben: nein

## 10. Dokumentation

- Architektur: Runtime-Contract, Drift-Contract, BVR-Core-Freeze
- Operator-Runbooks: GUI-Runtime, Deploy/Drift
- FAQ DE/EN/FR/NL: `docs/faq/PI_RS_BVR_GUI_DCC_001_FAQ.*`
- Wissensdatenbank DE/EN/FR/NL: GUI_HTTP_SERVER_FAILED, BVR_STATUS_AND_FALLBACK, VERSION_AND_DEPLOY_DRIFT
- Changelog: Unreleased-Eintrag
- Release Notes Payload: `RELEASE_NOTES_1_10_1_1.md`
- Statusmatrix/Roadmap: über Evidence/Status; vollständige Roadmap-Zeile optional nachziehen
- OpenAPI: neuer Endpoint dokumentiert im Code/Route; Profil-Gate beachten

## 11. Tests

- Unit GUI-HTTP / Launcher-Contract / Watchdog-Negativ / DCC-Status / Drift / Payload-Pin 1.10.1.1: **OK**
- i18n Locale-Gate-Skript: **OK**
- Regression BVR-Core: unverändert belassen (Freeze)
- physisch: BVR grün, GUI nicht sichtbar
- Gesamt (Auftrag): **`passed_with_gui_fallback`**

## 12. Payload und USB

- neue Version: **1.10.1.1**
- Buildmodus: `payload_repack` (Inject in Live-Squash)
- Build-Commit: `4098f004`
- Payload-SHA256: `2c0a1552831219e399c7496c353bbf343d13eb0a5e042b1293639d22e22fbbb2`
- Inhalts-/Locale-Prüfung: OK
- USB-Gerät: `/dev/sda` Ultra Line `24111412110686` (SETUPHELFER + SETUP_LOGS)
- USB-Update / Verify: OK

## 13. Physischer MSI-Retest

### Lauf A (blockiert) — `e2e-rescue-msi-20260722-000531-f1b86cfe`
- `run_control_invalid` (`disabled`, `already_consumed`) → Sofort-Shutdown ~18 s
- Partial-Import

### Lauf B (maßgeblich) — `e2e-rescue-msi-20260722-002744-a8f0a50d`
- Gerät: MSI GE63 Raider RGB 8RF
- Payload: 1.10.1.1
- GUI sichtbar: **nein**
- Locale (Health): de-DE
- HTTP ready: **ja**
- Chromium sichtbar: **nein** (Operator)
- Fallback: **ja** (`openvt_console_2_not_released`)
- Backup / Verify / Restore / Manifest: **passed**
- Auto-Shutdown: ja
- Evidence importiert: ja (offiziell + GUI-Incidental)
- TUI: Fortschritt inkonsistent (bis 11., Springen, „unten raus“) — `auto-e2e-state` hing hinter realem Ablauf

## 14. Watchdog-Negativtest

- automatisiert: Fallback bei GUI-Fail → `passed_with_gui_fallback`, kein Fake-Green: **bestanden**
- physisch: Fallback aktiv und BVR fortgesetzt: **bestanden**
- Ausgangszustand: Watchdog nicht entfernt

## 15. Endstatus

Zulässiger Wert: **`passed_with_gui_fallback`**

Begründung: BVR-Kern und HTTP-Fix physisch nachgewiesen; grafische Fortschrittsseite für den Operator **nicht** sichtbar; TUI-Fallback mit inkonsistenter Anzeige.

Nicht `passed`, weil Gate B (GUI sichtbar / kein unbeabsichtigter Fallback) fehlt.

## 16. Offene Punkte

- Blocker für volles `passed`: Chromium/VT-Handoff (`openvt_console_2_not_released`), echte GUI-Sichtbarkeit
- Warnungen: TUI-Progress-Sync (`auto-e2e-state` vs. echte Phasen); DCC im release-Profil
- technische Schulden: widersprüchliche Fallback-Statusdateien (`msi_compat_nomodeset` vs. `mode=gui`)
- nächster empfohlener Auftrag: **PI-RS-BVR-GUI-VT-001** — openvt/VT7/Chromium sichtbar + stabile TUI-Progress-Anzeige

---

## Gate-Kurzmatrix

| Gate | Ergebnis |
|------|----------|
| A BVR-Core | passed |
| B GUI sichtbar | **failed** |
| C Fallback | passed (aktiv, BVR sicher) |
| D i18n Payload | passed (Progress-Locales) |
| E DCC | partial (Modell ok, Profil blockiert) |
| F Version/Drift | yellow/green Feature-Identitäten |
| G Deploy /opt | deployed_with_warning |
| H Dokumentation | passed |
| I Evidence | passed (importiert) |
