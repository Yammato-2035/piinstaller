# QEMU 212528 — Fleet / Host Ingest Review

**Session:** `fleet-qemu_rescue_developer_autopilot_20260603_212528`  
**Ingest unter release:** Fleet-Routen erwartbar `PROFILE_ROUTE_BLOCKED` (kein local_lab-Umschalten in diesem Auftrag).

## Fleet Session (Persistenz `/opt`)

| Feld | Wert |
|------|------|
| Fleet session seen | **yes** |
| `status` | `timeout` |
| `agent_state` (final) | `booting` |
| `findings` | `qemu_timeout_124`, `guest_report_missing` |
| `guest.report_seen` | **false** |
| `guest.dev_server_report_new` | **false** |
| `serial.size_bytes` | **133 260** |
| `qemu.exit_code` | **124** |

## Host Devserver

| Feld | Wert |
|------|------|
| `dev_server_reports_before` | 0 |
| `dev_server_reports_after` | 0 |
| `report_new` false | **bestätigt** |
| Neue Reports aus Run 212528 | **keine** (nur ältere Smoke-Reports vom 2026-05-30) |

## Release Restore

| Feld | Wert |
|-------|------|
| release restored after | **yes** (Operator-Trap; `/api/version` → `release`, gate green) |

## Status

**`guest_report_missing`**

Fleet-Evidence vorhanden; kein Host-Ingest neuer Guest-Reports.
