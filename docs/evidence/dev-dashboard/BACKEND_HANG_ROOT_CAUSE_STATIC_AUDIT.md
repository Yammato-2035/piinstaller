# Backend Hang — statische Root-Cause-Analyse

**Datum:** 2026-05-28

## Kurzfassung

Ein **Hang** (systemd active, Port LISTEN, HTTP timeout) entsteht typischerweise, wenn der **einzelne Uvicorn-Worker** durch einen langen synchronen Request blockiert ist — nicht weil `/health` selbst schwere Arbeit leistet.

## /health und /api/version (nach Härtung)

| Endpunkt | Blockierend? | Hinweis |
|----------|--------------|---------|
| `/health` | Nein | `core.liveness.build_health_payload` — JSON-Cache, kein Git/Dashboard |
| `/api/version` | Minimal | `load_project_version()` + optional Git nur mit `SETUPHELFER_VERSION_INCLUDE_GIT=1` |

## Dashboard-Pfad (Haupt-Risiko)

- `dev_dashboard_status` synchronisierte alle `BACKUP_JOBS` mit systemd.
- `_compute_deploy_drift` vergleicht viele Manifest-Dateien (git show, SHA256).
- `enrich_dashboard_cockpit` lädt Roadmap, Tests-Evidence, Structure-Health.

**Mitigation in diesem Lauf:** Abschnitts-Timeouts (`_bounded_section`), `asyncio.to_thread` + Gesamt-Timeout für Status-Route.

## Startup (Lifespan)

`_app_lifespan` lädt Config und optional OLED-Autostart — kann Start verzögern, blockiert aber nicht `/health` nach Listen, sofern Worker frei ist.

## JSON

`backend_hang_root_cause_static_audit_latest.json`
