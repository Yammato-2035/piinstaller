# DCC — Report Freshness & Filters

- **Repo-Berichte:** `GET /api/dev-dashboard/recent-evidence` (local_lab), Default `limit=5`.
- **Agent-Uploads:** Dev-Server `latest_findings` — separat, nicht mit Repo-Evidence verwechseln.
- **Filter:** `category`, `status`, `time_range`, `search`.
- **Sortierung:** `**Datum:**` in MD / JSON timestamps, Fallback Datei-mtime.
