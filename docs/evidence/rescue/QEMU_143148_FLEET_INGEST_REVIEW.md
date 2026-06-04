# QEMU 143148 — Fleet / Host Ingest

| Prüfung | Ergebnis |
|---------|----------|
| Fleet-Session (Operator-Log) | `fleet-qemu_rescue_developer_autopilot_20260604_143148` |
| Fleet final (Smoke-Summary) | `guest_found=false`, `report_new=false` |
| `guest_report_missing` | **yes** (kein neuer Dev-Server-Report) |
| `dev_server_reports_after` | **0** (Smoke-JSON) |
| Release nach QEMU | **yes** (Trap: `install_profile=release`) |
| Host-Ingest sichtbar | **no** — kein POST (CLI startet nicht) |

## Release-Route-Check (aktuell)

`GET /api/fleet/sessions` → **404** `PROFILE_ROUTE_BLOCKED` (erwartet unter `release`).

Evidence: `qemu_143148_fleet_release_block_latest.txt`
