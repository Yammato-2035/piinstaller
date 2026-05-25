# Deploy Helper Integration Result

**Datum:** 2026-05-25  
**Workspace-HEAD vor Aenderung:** `27d790a`  
**Runtime-Smoke:** success

## Ergebnis

Der kontrollierte Deploy-Helper fuer das Development Dashboard wurde umgesetzt, produktiv installiert und gegen die Runtime unter `/opt/setuphelfer` erfolgreich verifiziert:

- read-only Deploy-Statusvertrag im Backend
- kontrollierter Deploy-Orchestrator ohne Direktaufruf von `deploy-to-opt.sh`
- Root-Helper-Skript mit festem Workspace, Lockfile und persistenter State-Datei
- `systemd`-Oneshot-Unit fuer den privilegierten Schritt
- optionales, eng begrenztes `sudoers`-Beispiel
- Deploy-Panel und Update-Karte im Dashboard

## Sicherheitsgrenzen

Die neue Strecke erlaubt **nicht**:

- beliebige Root-Shell
- `apt install/upgrade`
- `dd`
- `mkfs`
- `parted`
- Backup / Restore
- USB-Write
- Direktaufruf von `deploy-to-opt.sh` aus dem unprivilegierten Backend

## Persistente Evidence

Der neue Pfad verwendet:

- `/var/lib/setuphelfer/deploy-jobs/latest.json`
- `/var/lib/setuphelfer/deploy-jobs/latest.log`

Tests koennen ersatzweise `build/dev-dashboard/deploy-jobs/` nutzen.

## Dashboard-Funktion

Neu im Development Dashboard:

- Panel **Deploy / Runtime-Synchronisation**
- Anzeige von Runtime-Gate, Deploy-Drift, Workspace HEAD, Runtime-Pfad, Manifest-Match, betroffenen Dateien und letztem Job
- Button fuer:
  - Status aktualisieren
  - Logs anzeigen
  - Operator-Setup anzeigen
  - Deploy anfordern (nur mit Confirm-Dialog)

Neu als kleine Karte:

- **Version / Update**
- nur lokale Konsistenzpruefung
- kein Auto-Update
- keine Paketmanager-Aktion

## Operator-Setup

Die produktive Installation der `systemd`-Unit und des Root-Skripts wurde manuell mit `sudo` durchgefuehrt; das optionale, eng begrenzte `sudoers`-Snippet bleibt nur ein Development-Hilfsmittel.

## Runtime-Abnahme

Verifiziert auf der produktiven Runtime:

- `/var/lib/setuphelfer/deploy-jobs/latest.json`:
  - `status = success`
  - `deploy_exit_code = 0`
  - `runtime_gate_exit_after = 0`
- `./scripts/check-runtime-deploy-gate.sh`:
  - Exit `0`
- `GET /api/version`:
  - HTTP `200`
  - `backend_runtime_path = /opt/setuphelfer/backend`
- `GET /api/dev-dashboard/deploy/status`:
  - `status = success`
  - `runtime_gate.exit_code = 0`
  - `deploy_drift.status = green`
- `GET /api/dev-dashboard/update/status`:
  - `status = ok`
  - `deploy_required = false`
  - `automatic_update_allowed = false`
  - `package_manager_update_allowed = false`
- `GET /api/dev-dashboard/deploy/logs`:
  - `status = success`
  - Log-Tail endet mit `final_status=success`

## Folgehaertungen waehrend der Runtime-Abnahme

Fuer den produktiven Lauf wurden zusaetzlich verifiziert bzw. nachgezogen:

- `deploy-to-opt.sh` behandelt schreibgeschuetzte Desktop-Entry-/systemnahe Nebenpfade als Warnung statt als Deploy-Abbruch
- die Deploy-/Update-/Rescue-Statusaggregation verwendet fuer das Runtime-Gate eine interne read-only Auswertung statt eines Backend-Self-Calls ueber `curl`
- `start-browser-production.sh` wartet kurz auf das Backend, damit `setuphelfer.service` nach einem Deploy ohne manuellen Zweit-Restart stabil startet
- die Cockpit-Ansicht `?window=cockpit` zeigt jetzt ebenfalls `Deploy / Runtime-Synchronisation` und `Version / Update`

## Teststand

Erfolgreich:

- `py_compile` fuer:
  - `backend/core/deploy_job_state.py`
  - `backend/core/deploy_orchestrator.py`
  - `backend/core/update_check.py`
  - `backend/app.py`
- neue Unit-Tests:
  - `backend.tests.test_deploy_orchestrator_v1`
  - `backend.tests.test_deploy_job_state_v1`
  - `backend.tests.test_update_check_v1`
- geforderte Regression:
  - `backend.tests.test_rescue_iso_build_dashboard_state_v1`
  - `backend.tests.test_rescue_iso_build_executor_v1`
  - `backend.tests.test_deploy_runner_rescue_stick_readonly_build_emulation_v1`
  - `backend.tests.test_partitions_storage_facade_v1`
  - `backend.tests.test_partitions_hardstop_preview_v2`
  - `backend.tests.test_partitions_manifest_layout_preview_v2`
  - `backend.tests.test_partitions_restore_handoff_preview_v2`
- Frontend-Build:
  - `npm --prefix frontend run build`

## Phase-0 / Runtime-Gate

Der urspruengliche Blocker `Exit 14` (`deploy_drift` auf `backend/app.py`) ist durch den kontrollierten Helper-Deploy aufgehoben.
Der finale Phase-0-Lauf liefert:

- Exit `0`
- `deploy_drift.status = green`
- `manifest_match = true`

## Fazit

Die Architektur fuer den sicheren, kontrollierten Deploy ist umgesetzt, produktiv installiert und gegen die laufende Runtime erfolgreich abgenommen.
Deploy-Gate, Deploy-/Update-API und Cockpit-UI sind fuer diesen Scope **gruen**; automatische Updates, Paketmanager-Aktionen und verbotene Schreibpfade bleiben weiterhin ausgeschlossen.
