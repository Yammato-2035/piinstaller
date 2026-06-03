# DCC Report Freshness — Backend Review

**Status:** `stale_source_path_gap` → Fix in `dev_dashboard_recent_evidence.py`

| Frage | Antwort |
|-------|---------|
| Funktion „letzte Berichte“ (alt) | `build_dev_server_section()` → `storage.list_reports()` |
| Control-Center Evidence (alt) | `build_evidence_section()` → `build_evidence_index()` mtime-Walk |
| Neue Quelle | `build_recent_evidence_feed()` — Whitelist unter `docs/evidence/{rescue,dev-dashboard,...}` |
| Sortierung | Embedded `**Datum:**` / JSON timestamps, Fallback mtime |
| API | `GET /api/dev-dashboard/recent-evidence?limit=5&category=&status=&search=&time_range=` |
| Summary | `build_evidence_section()` liefert `recent_reports`, `recent_tests`, `default_limit: 5` |

**Rescue/QEMU-Pfade:** jetzt in `_EVIDENCE_ROOTS` enthalten.
