# DCC Report Freshness — Fix Decision

1. **Repo-Evidence-Feed** (`dev_dashboard_recent_evidence.py`): Whitelist-Scan, kein Shell.
2. **Sortierung:** Embedded Datum bevorzugt (Regex inkl. reines `YYYY-MM-DD`), sonst mtime.
3. **Defaultlimit:** 5 (`recent_reports`, `recent_tests`, manual-command-runs).
4. **Filter:** category, status, time_range (`today|24h|7d|all`), search.
5. **Dev-Server:** `latest_findings` bleibt Agent-Uploads — klar getrennt beschriftet.
6. **Kein Fake-Green:** Status aus Dateiname/JSON, nicht pauschal ok.
