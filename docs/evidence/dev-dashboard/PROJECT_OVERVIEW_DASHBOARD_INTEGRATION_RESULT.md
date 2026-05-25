# Project Overview Dashboard Integration Result

**Datum:** 2026-05-25
**Status:** runtime_verified

## Ziel

Eine read-only Projektuebersicht sollte weitere Dashboard-Bereiche ehrlich auf gruen/gelb bringen, ohne Backup, Restore, Packaging-Installation, ISO-Build oder andere riskante Aktionen auszufuehren.

## Umgesetzt

- neuer read-only State `backend/core/project_overview_dashboard_state.py`
- neuer read-only State `backend/core/packaging_readiness_state.py`
- neue API-Endpunkte:
  - `GET /api/dev-dashboard/project-overview`
  - `GET /api/dev-dashboard/packaging/readiness`
- neue Green-Up-Tests:
  - `backend/tests/test_dev_dashboard_greenup_status_v1.py`
  - `backend/tests/test_packaging_artifacts_readiness_v1.py`
  - `backend/tests/test_dashboard_ui_safety_static_v1.py`

## Statusregeln

- Runtime / Deploy Helper / Update Check koennen gruen sein, auch wenn Rescue ISO nur gelb bleibt
- Rescue ISO bleibt bei Prebuild-ok aber ohne ISO absichtlich `yellow`
- USB Write bleibt blockiert und wird als Safety-Gate `green`
- Packaging zeigt nur Readiness, nie `install_test_passed=true`
- Monolith bleibt absichtlich `yellow`, solange zentrale Kopplung in `backend/app.py` fortbesteht
- Testregister kann als Uebersicht `green` sein, auch wenn offene Testfelder separat `yellow`/`red` bleiben

## Lokal verifiziert

- `backend/venv/bin/python3 -m py_compile ...` fuer neue State-Dateien und `backend/app.py`
- `PYTHONPATH=backend backend/venv/bin/python3 -m unittest ... -v` mit Green-Up-, Deploy-, Update- und Rescue-Suiten
- statische UI-Safety-Pruefung ohne gefaehrliche Runtime-Aktionen
- final bestaetigt:
  - `82` Tests `OK`
  - `41` Regressionstests `OK`

## Produktive Runtime-Abnahme

Verifiziert nach dem finalen Helper-Deploy `deploy-20260525T193756Z-954998`:

- `/var/lib/setuphelfer/deploy-jobs/latest.json`
  - `status = success`
  - `deploy_exit_code = 0`
  - `runtime_gate_exit_after = 0`
  - `workspace = /home/volker/piinstaller`
  - `runtime_path = /opt/setuphelfer`
- SHA256 Workspace == `/opt` fuer:
  - `backend/core/rescue_iso_build_executor.py`
  - `backend/core/rescue_iso_build_state.py`
  - `backend/core/packaging_readiness_state.py`
  - `backend/core/project_overview_dashboard_state.py`
  - `backend/app.py`
- `GET /api/dev-dashboard/project-overview`
  - `status = yellow`
  - `runtime.overall_status = green`
  - `deploy_helper.overall_status = green`
  - `update_check.overall_status = green`
  - `rescue_iso.overall_status = yellow`
  - `dpkg_preflight.overall_status = green`
  - `usb_write_gate.overall_status = green`
  - `packaging.overall_status = green`
  - `roadmap.overall_status = green`
  - `tests.summary_status = green`
  - `monolith.overall_status = yellow`
  - `evidence.overall_status = green`
- `GET /api/dev-dashboard/packaging/readiness`
  - `status = green`
  - `deb_ready = true`
  - `rpm_ready = true`
  - `appimage_ready = true`
  - `install_test_passed = false`
  - `install_test_pending = true`
  - keine Installations- oder Root-Aktionen erlaubt

## Verbotene Aktionen weiterhin nicht ausgefuehrt

- kein ISO-Build
- kein `lb build`
- kein USB-Write
- kein `dd`
- kein `mkfs`
- kein `parted write`
- kein Backup / Restore / Verify Deep
- keine Paketinstallation

## Bewertung

Die neue read-only Projektuebersicht macht mehrere Governance-Bereiche ehrlich sichtbar:

- `green`: Runtime, Deploy Helper, Update Check, DPKG Preflight, USB-Write-Safety-Gate, Packaging-Readiness, Roadmap, Testregister, Evidence-Index
- `yellow`: Rescue-ISO-Gesamtbereich ohne echte ISO, Monolith-Uebersicht

Backup, Restore und Live-Boot werden durch diese Erweiterung weiterhin nicht kosmetisch gruen.
