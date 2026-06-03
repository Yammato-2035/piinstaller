# Developer Backend Watchdog

**Stand:** 2026-06-03  
**Status:** `architecture_ready`

## Problem

Ein Backend-Prozess kann seinen eigenen Totalausfall nicht zuverlässig melden. Ist der Prozess tot oder hängt er ohne HTTP-Antwort, liefert `/api/version` und interne Dashboard-Logik nichts Verwertbares. Port **LISTEN** allein beweist keine funktionierende API.

## Entscheidung

| Schicht | Rolle |
|---------|--------|
| **Externer Healthcheck** | `scripts/dev-dashboard/check-backend-health.sh` — außerhalb des Backend-Prozesses, read-only |
| **Evidence** | `docs/evidence/dev-dashboard/backend_health_latest.json` + `backend_health_history.jsonl` |
| **DCC-Anzeige** | `GET /api/dev-dashboard/backend-health` (nur `local_lab` / `dev_control_enabled`) — liest nur Dateien |
| **Deploy-Härtung** | `deploy-to-opt.sh`: `daemon-reload` vor Restart, Retry auf `/api/version`, Exit ≠ 0 bei Ausfall |
| **Optionaler Timer** | `packaging/systemd/setuphelfer-dev-healthcheck.*.example` — **nicht** automatisch aktiv |

## Nicht-Ziele

- Kein Dashboard-Autorestart ohne Operator-Freigabe
- Kein freier Shellzugriff aus dem DCC
- Kein öffentliches Produktfeature (developer-only)
- Kein Ersatz für Phase-0-Gates vor Rescue/Backup

## Watchdog-Felder (Evidence JSON)

- `backend_service_active`, `backend_port_8000_listening`
- `api_version_http`, `install_profile`, `profile_gate_status`, `dev_control_enabled`
- `dev_dashboard_status_http`, `fleet_sessions_http`, `recent_evidence_http`
- `frontend_port_3001_listening`, `web_ui_http`
- `expected_profile_blocks` (release: 404 `PROFILE_ROUTE_BLOCKED` = erwartet)
- `overall_status`, `failure_classification`, `recommended_operator_action`
- `last_ok_at`, `last_failure_at`
- `repo_root`, `evidence_dir`, `latest_path`, `history_path`, `script_path`, `cwd` (im Evidence-JSON)

## Evidence-Lesbarkeit

Healthcheck setzt **`chmod 664`** auf Evidence-Dateien (setgid-Gruppe `setuphelfer`). Ohne Gruppen-Leserecht meldet die API fälschlich `unknown` (Backend-User kann `600`-Dateien des Operators nicht lesen). Loader liefert `searched_paths` und unterscheidet `permission_denied`.

## Verwandte Dokumente

- MVP-Entscheidung (älterer `/health`-Timer): `docs/architecture/BACKEND_WATCHDOG_MVP_DECISION.md`
- Operator: `docs/runbooks/DEVELOPER_BACKEND_WATCHDOG_RUNBOOK.md`
- Evidence: `docs/evidence/dev-dashboard/DEVELOPER_BACKEND_WATCHDOG_RESULT.md`
