# Developer Backend Watchdog — Release Restore Result

**Datum:** 2026-06-03

## Durchführung

local_lab-Smoke **nicht** ausgeführt (Deploy blockiert). Runtime blieb durchgehend **release**.

| Feld | Wert |
|------|------|
| install_profile | **release** |
| profile_gate_status | **green** |
| dev_control_enabled | **false** |
| `/api/dev-dashboard/backend-health` | **PROFILE_ROUTE_BLOCKED** (erwartet ohne Deploy+local_lab) |
| **Status** | **ok** (Release unverändert korrekt) |

Release-Restore-Schritt nach Smoke: **n/a** (kein Profilwechsel in diesem Lauf).
