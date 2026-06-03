# DCC Report Freshness — Release Restore Result

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| local_lab aktiviert | **no** (Deploy-Smoke blockiert) |
| install_profile | `release` (unverändert) |
| profile_gate_status | `green` |
| dev_control_enabled | `false` |

`/api/dev-dashboard/recent-evidence` unter release: **PROFILE_ROUTE_BLOCKED** (erwartet, Route nicht live ohne Deploy+local_lab).

**Status:** `ok` (Release war durchgehend aktiv; kein Profilwechsel nötig)
