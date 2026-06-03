# DCC Report Freshness — Live Smoke

**Runtime:** `release`, `dev_control_enabled=false`

| Prüfung | Ergebnis |
|---------|----------|
| `GET /api/dev-dashboard/recent-evidence` | **PROFILE_ROUTE_BLOCKED** (erwartet) |
| `GET /api/dev-dashboard/control-center-summary` | **PROFILE_ROUTE_BLOCKED** (erwartet) |

**Status:** `skipped_release_profile`

Verifikation: Unit-Tests + Workspace-Scan (June-2026-Reports zuerst).
