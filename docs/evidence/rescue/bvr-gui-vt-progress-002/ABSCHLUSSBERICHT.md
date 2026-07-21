# PI-RS-BVR-GUI-VT-PROGRESS-002 – Abschlussbericht

## 1. Workspace und Git

- Workspace: `/tmp/piinstaller-vt-progress-002` (sauberer Worktree; Hauptbaum `/home/volker/piinstaller` bleibt mit fremder Drift unangetastet)
- Git-Root: `/tmp/piinstaller-vt-progress-002`
- Repository: `piinstaller`
- Ausgangsbranch: `pi-rs-bvr-gui-dcc-001-http-i18n-drift-deploy` @ `92bfcc15`
- Feature-Branch: `pi-rs-bvr-gui-vt-progress-002-impl` → Merge nach `pi-rs-bvr-gui-vt-progress-002`
- HEAD vorher: `92bfcc15`
- HEAD nachher: `813aed98` (Worktree-Branch `pi-rs-bvr-gui-vt-progress-002-impl`; Ref `pi-rs-bvr-gui-vt-progress-002` ebenfalls)
- origin/main: enthalten (Baseline-Ancestor-Check Phase 0)
- `92bfcc15` enthalten: ja
- `71717ec5` enthalten: ja
- `6d90ab3e` enthalten: ja
- Commits: `6f4b5e4b`, `2adffe57`, `0ff0e6dd`, `813aed98`
- Push: noch nicht (Freigabe erforderlich auf `origin/pi-rs-bvr-gui-vt-progress-002`)
- fremde Drift: unangetastet im Haupt-Worktree
- unerwartete Drift: keine im sauberen Worktree

## 2. Baseline

- Run-ID: `e2e-rescue-msi-20260722-002744-a8f0a50d`
- Payload: `1.10.1.1`
- BVR: passed
- HTTP: ready
- GUI: nicht sichtbar (Operator)
- Fallback: Evidence-Code `openvt_console_2_not_released` (**stale**); Live-Log zeigt VT7 + Chromium `auto-e2e-progress.html`
- TUI-Fortschritt: `sabrent_waiting`
- tatsächlicher Fortschritt: `shutdown`
- Gesamtstatus: `passed_with_gui_fallback`

## 3. VT-/X11-Root-Cause

- primäre Ursache: Watchdog-Health prüfte `rescue.html` / `chromium.*rescue.html`, Kiosk lud `auto-e2e-progress.html` → Health nie OK → Timeout → Kill → TUI
- sekundäre Ursachen: stale Fallback-JSON; Progress-Source-Drift; Legacy-Fehlername „console_2“ trotz VT7
- TUI-VT: 1
- bisheriger GUI-VT: 7
- Confidence: **high**

## 4. VT-/GUI-Fix

- Auswahlverfahren: `setuphelfer_rescue_select_gui_vt` (7→8→9), nie VT1, kein `fuser -k`
- Sichtbarkeit: HTTP health + X ready + Chromium-URL + Fenster + aktiver VT
- strukturierte Codes: `rescue.gui.*`
- BVR-Core verändert: **nein**

## 5. Fortschrittsmodell

- autoritative Quelle: `canonical-bvr-progress.json`
- physical-progress: Projektion
- auto-e2e-state: Orchestrierung + Drift-Erkennung
- Driftcode: `rescue.bvr.progress_source_drift`

## 6. DCC / Release-Profil

- Developer-Endpunkt bleibt geschützt
- neu: `GET /api/status/rescue-bvr` (read-only, redigiert)

## 7. i18n

- de-DE / en-US / fr-FR / nl-NL: Key-Parität (43 Keys)

## 8–10. Dokumentation / Tests / Deploy

- Architektur-Contracts + FAQ/KB/Operator-Docs
- Unit-Tests: 34 focused passed
- Deploy/USB/MSI: **ausstehend** (Operator)

## 12. Physischer MSI-Retest

- **noch nicht ausgeführt**

## 15. Endstatus

**`implemented_pending_physical_retest`**

## 16. Offene Punkte

- Payload-Build 1.10.1.2 + USB-Update
- `/opt`-Deploy über `deploy-to-opt.sh`
- Physischer MSI-Retest mit Sichtbarkeitsnachweis
- Kontrollierter Fallback-Negativtest
