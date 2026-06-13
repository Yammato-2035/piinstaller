# DCC Status Route Audit E.11

**Kampagne:** A.4 · **Version:** 1.7.15.0

## Vorher

- `GET /api/dev-dashboard/status` in `app.py`
- Direkte Übergabe `BACKUP_JOBS`, `_sync_stale_runner_job_from_systemd`, `_job_snapshot`, `_detect_active_package_operations` an `build_dev_dashboard_status`

## Nachher

- Route: `backend/api/routes/dev_dashboard_readonly.py`
- Entry: `dcc_status_facade.build_dcc_dashboard_status_api`
- Runtime-Adapter: `core/dcc_status_runtime.py` (`get_dashboard_status_runtime_adapters`)
- Service: `dev_dashboard_status_service.build_dev_dashboard_status` (unverändert)
- Aggregation: `build_dashboard_status_body` via Facade (unverändert)

## Entfernte Kopplungen

- `app.py` enthält keine DCC-Status-Route mehr
- Router importiert `app` nicht für Job-State (nur Logger)

## API/UI

Keine Response-Änderung (statische Tests grün).
