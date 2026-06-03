# DCC — Report Freshness & Filters

- **Repo-Berichte:** `GET /api/dev-dashboard/recent-evidence` (local_lab), Default `limit=5`.
- **Agent-Uploads:** Dev-Server `latest_findings` — separat, nicht mit Repo-Evidence verwechseln.
- **Filter:** `category`, `status`, `time_range`, `search`.
- **Sortierung:** `**Datum:**` in MD / JSON timestamps, Fallback Datei-mtime.

## Deploy / Live (2026-06-03)

- Fix committed (`aa52071` / `e3d7da9`); **Live unter `/opt` erfordert** `sudo ./scripts/deploy-to-opt.sh`.
- Agent-Deploy-Versuch: **blocked** (sudo password) — siehe `DCC_REPORT_FRESHNESS_DEPLOY_LIVE_RESULT.md`.
- Nach Operator-Deploy: kurz `curl (7)` + `daemon-reload` Warnung → Recovery → API live unter `local_lab`; siehe `BACKEND_RECOVERY_AFTER_DCC_DEPLOY_RESULT.md`, `DCC_REPORT_FRESHNESS_API_LIVE_AFTER_RECOVERY.md`.
- Nach **Release-Restart** (`daemon-reload` + restart): erneut kurz `:8000` down → recovered unter **release**; Gates grün; `recent-evidence` → `PROFILE_ROUTE_BLOCKED`; siehe `BACKEND_DOWN_AFTER_RELEASE_RESTART_RESULT.md`.
- **Developer Backend Watchdog:** externer Healthcheck `scripts/dev-dashboard/check-backend-health.sh` → Evidence JSON; DCC-Panel + `GET /api/dev-dashboard/backend-health` (nur local_lab); siehe `DEVELOPER_BACKEND_WATCHDOG_RESULT.md`.
- **Watchdog Deploy live (2026-06-03):** Drift bestätigt (`/opt` ohne Skript/Loader/Bundle); Agent-Deploy blockiert (sudo); Workspace-Healthcheck ok; Operator-Deploy ausstehend — `DEVELOPER_BACKEND_WATCHDOG_DEPLOY_LIVE_RESULT.md`.
