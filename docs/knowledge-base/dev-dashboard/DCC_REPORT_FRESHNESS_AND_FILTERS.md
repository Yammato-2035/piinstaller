# DCC — Report Freshness & Filters

- **Repo-Berichte:** `GET /api/dev-dashboard/recent-evidence` (local_lab), Default `limit=5`.
- **Agent-Uploads:** Dev-Server `latest_findings` — separat, nicht mit Repo-Evidence verwechseln.
- **Filter:** `category`, `status`, `time_range`, `search`.
- **Sortierung:** `**Datum:**` in MD / JSON timestamps, Fallback Datei-mtime.

## Deploy / Live (2026-06-03)

- Fix committed (`aa52071` / `e3d7da9`); **Live unter `/opt` erfordert** `sudo ./scripts/deploy-to-opt.sh`.
- Agent-Deploy-Versuch: **blocked** (sudo password) — siehe `DCC_REPORT_FRESHNESS_DEPLOY_LIVE_RESULT.md`.
- Nach Operator-Deploy: kurz `curl (7)` + `daemon-reload` Warnung → Recovery → API live unter `local_lab`; siehe `BACKEND_RECOVERY_AFTER_DCC_DEPLOY_RESULT.md`, `DCC_REPORT_FRESHNESS_API_LIVE_AFTER_RECOVERY.md`.
