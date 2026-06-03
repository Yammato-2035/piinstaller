# DCC Report Freshness — Status API Review

**Datum:** 2026-06-03

**Status:** `blocked` — kein Post-Deploy-Lauf.

## Design (Repo)

- **Neue API:** `GET /api/dev-dashboard/recent-evidence` (Filter, limit)
- **Control-Center-Summary:** `evidence.recent_reports`, `evidence.recent_tests` via `build_evidence_section()`
- **UI:** `RecentEvidenceFeedPanel` ruft API (oder Summary-Initialdaten) auf

Unter **release:** beide Routen `PROFILE_ROUTE_BLOCKED` (erwartet).
