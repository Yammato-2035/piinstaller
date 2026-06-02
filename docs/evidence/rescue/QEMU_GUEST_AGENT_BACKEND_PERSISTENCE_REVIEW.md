# QEMU Guest Agent — Backend Persistence Review

**Run-ID:** `qemu_rescue_developer_autopilot_20260602_202725`

## Fleet Session (Persistenz)

Quelle: `/opt/setuphelfer/docs/evidence/runtime-results/dev-dashboard/fleet_sessions.jsonl` (letzter Eintrag)

| Feld | Wert |
|------|------|
| session_id | `fleet-qemu_rescue_developer_autopilot_20260602_202725` |
| status (final) | **timeout** |
| agent_state | booting |
| qemu.exit_code | **124** |
| serial.size_bytes | **0** |
| findings | `serial_empty`, `classification_hint_serial_empty_boot_unknown`, `qemu_timeout_124`, **`guest_report_missing`** |
| guest.report_seen | **false** |
| guest.dev_server_report_new | **false** |

## Dev-Server Summary

| Feld | before | after |
|------|--------|-------|
| reports_last_24h | 0 | 0 |
| report_new | — | **false** |

Kein neuer Guest-Report während des Laufs.

## Rescue-Agent Sessions

Kein Rescue-Agent-Ingest für diesen Run in Persistenz sichtbar.

## Bewertung

**Status: backend_session_found_no_guest**

Fleet-Session vorhanden und korrekt als Timeout/`guest_report_missing` klassifiziert. Kein Guest-Report, kein `guest_found`.

API in `release` nach Smoke: `PROFILE_ROUTE_BLOCKED` (erwartet).
