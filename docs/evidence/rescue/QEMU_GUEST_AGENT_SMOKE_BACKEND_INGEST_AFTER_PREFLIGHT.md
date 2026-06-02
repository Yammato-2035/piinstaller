# QEMU Guest Agent Smoke — Backend Ingest After Preflight

**Datum:** 2026-06-03  
**Run:** `qemu_rescue_developer_autopilot_20260602_202725`

## Fleet Session (Persistenz `/opt/setuphelfer`)

| Feld | Wert |
|------|------|
| Fleet Session für RUN_ID vorhanden | **yes** |
| Fleet final status | **timeout** |
| Fleet findings | `serial_empty`, `qemu_timeout_124`, `guest_report_missing` |
| guest report seen | **no** (`guest.report_seen=false`) |
| rescue-agent session seen | **no** |
| report_new | **false** |
| guest_found | **false** |

## Dev-Server Reports

| Feld | Wert |
|------|------|
| reports_before → after | 0 → 0 |
| dev_server_report_new | **false** |

Snapshots im Run-Dir: `dev_server_summary_before.json`, `dev_server_summary_after.json`, `dev_server_reports_after.json` — **kein** neuer Guest-Report.

**Status:** `blocked`

Keine Fleet-/Report-Evidence für einen post-Preflight-Smoke. Vor-Fix-Run bestätigt erneut `guest_report_missing` bei Serial 0 B.
