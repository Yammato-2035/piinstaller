# Deploy Helper Integration Result

**Datum:** 2026-05-25  
**Workspace-HEAD vor Aenderung:** `27d790a`  
**Runtime-Smoke:** pending

## Ergebnis

Der kontrollierte Deploy-Helper fuer das Development Dashboard wurde vorbereitet:

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

## Operator-Setup verbleibt manuell

Vor einer echten Runtime-Abnahme muss der Operator die systemd-Unit und das Root-Skript installieren; optional kann fuer Development ein eng begrenztes `sudoers`-Snippet gesetzt werden.

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

Noch offen in diesem Dokumentationsstand:

- realer Runtime-Smoke nach Installation des Helpers

## Phase-0 / Runtime-Gate

Zum Zeitpunkt der Implementierung liefert das Runtime-Gate:

- Exit `14`
- `deploy_drift.status = yellow`
- betroffene Datei: `backend/app.py`
- `manifest_match = true`
- `suggested_actions = [deploy_backend_files, restart_backend_manual]`

Das ist dokumentiert und **kein** gruener Runtime-Smoke.

## Fazit

Die Architektur fuer den sicheren, kontrollierten Deploy ist umgesetzt und lokal testbar.  
Die produktive Runtime-Abnahme bleibt **pending**, bis Operator-Setup und ein realer Deploy ueber die neue Helper-Strecke ausgefuehrt wurden.
