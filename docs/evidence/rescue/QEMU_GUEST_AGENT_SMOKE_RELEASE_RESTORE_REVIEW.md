# QEMU Guest Agent Smoke — Release Restore Review

**Datum:** 2026-06-03

## API nach Smoke (aktuell)

| Feld | Wert | Erwartung |
|------|------|-----------|
| install_profile | `release` | yes |
| profile_gate_status | `green` | yes |
| dev_control_enabled | `false` | yes |
| `/api/dev-dashboard/status` | HTTP 404 `PROFILE_ROUTE_BLOCKED` | yes |
| `/api/fleet/sessions` | HTTP 404 `PROFILE_ROUTE_BLOCKED` | yes |
| `/api/rescue-agent/sessions` | HTTP 404 `PROFILE_ROUTE_BLOCKED` | yes |

operator_smoke.log (Run `20260602_202725`) zeigt Release-Trap am Ende mit `install_profile=release`.

**Status:** `ok`

Release-Profil ist wiederhergestellt; Devserver korrekt deaktiviert.
