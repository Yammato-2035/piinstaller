# Rescue ISO Executor Dashboard — IST-Analyse

**Datum:** 2026-05-25  
**Git HEAD:** `27d790a`

## Vorhandene Dashboard-Funktionen

- `GET /api/dev-dashboard/status` liefert den Cockpit-Gesamtstatus.
- `GET /api/dev-dashboard/rescue-build/status` aggregiert bereits Rescue-Build-Evidence read-only.
- `ExternalDevelopmentControlCenter` und `DevelopmentDashboard` binden `RescueBuildPanel` bereits ein.
- Das Cockpit zeigt bereits Runtime-Gate, Deploy-Drift, Governance-Matrix und Rescue-Release-Kontext.

## Vorhandene Rescue-Build-Datenquellen

- `scripts/rescue-live/create-temp-runtime-bundle.sh`
- `scripts/rescue-live/validate-temp-runtime-bundle.sh`
- `scripts/rescue-live/prepare-controlled-live-build-tree.sh`
- `scripts/rescue-live/validate-controlled-live-build-tree.sh`
- `build/rescue/live-build/setuphelfer-rescue-live/auto/config`
- `build/rescue/live-build/setuphelfer-rescue-live/auto/build`
- `build/rescue/logs/controlled-iso-build/latest.log`
- `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`
- `docs/evidence/runtime-results/rescue/controlled_usb_write_latest_summary.json`
- `docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md`
- `docs/evidence/rescue/RESCUE_BIG_STEP_STATUS_PLAN.md`

## Fehlende Executor- und Logging-Funktionen vor dieser Integration

- Kein eigener API-Contract fuer den kontrollierten Rescue-ISO-Executor.
- Kein zentraler Step-Wrapper fuer `toolcheck`, `detect_stale_state`, Bundle/Tree-Prepare und Validatoren.
- Kein Action-Status pro Schritt mit `action_id`, Step-Log und Summary-Update.
- Kein eigener Operator-Command-Generator fuer `sudo clean` und `sudo lb build noauto`.
- Keine Stale-State-Erkennung fuer:
  - `.build/chroot_package-lists.install`
  - root-owned Dateien unter `.build/`, `chroot/`, `cache/`, `binary/`, `local/`
  - `skipping ... already done`
  - `tar failed` / `File exists` in `debootstrap.log`
- Kein Dashboard-Panel fuer Operator-required Kommandos als primaerer Weg.

## Risiken bei sudo und root-owned Build-State

- Root-owned Stage-Dateien blockieren sauberes User-Cleanup und koennen `lb`-Stages faelschlich als erledigt markieren.
- Stale Marker wie `chroot_package-lists.install` fuehren zu `skipping ... already done` und verwenden alte Paketlisten weiter.
- Teilweise debootstrap-/tar-Artefakte koennen spaetere Retries mit `tar failed` oder `File exists` abbrechen.
- Ein direktes Backend-`sudo` ohne kontrolliertes Konzept waere ein Safety-Risiko; deshalb muss der Default `operator_required` bleiben.

## Empfehlung fuer sichere Minimalintegration

1. Read-only Statevertrag in `backend/core/rescue_iso_build_state.py`
2. Expliziter Step-Executor in `backend/core/rescue_iso_build_executor.py`
3. Separater Operator-Command-Generator in `backend/core/rescue_iso_operator_commands.py`
4. Neue Cockpit-Routen unter `/api/dev-dashboard/rescue-iso/*`
5. Frontend-Panel mit:
   - Stale-State-Sichtbarkeit
   - Step-Buttons nur fuer erlaubte Schritte
   - Operator-Sudo-Kommandos statt Direkt-Build
   - Log-Tail und Summary ohne manuelle Terminalsammlung
6. USB-Write, `dd`, `mkfs`, `parted write`, Restore, Backup, Verify Deep bleiben strikt ausgeschlossen
