# QEMU Guest Agent Smoke — Autopilot Result Review

**Datum:** 2026-06-03  
**Quelle (einziger verfügbarer Run):** `qemu_rescue_developer_autopilot_20260602_202725`

> **Warnung:** Dieser Run ist **nicht** der post-Preflight-/post-ISO-Rebuild-Smoke. Er dient nur als letzter verfügbarer Evidence-Stand.

## qemu_autopilot_result.json

| Feld | Wert |
|------|------|
| qemu_started | **yes** (implizit, exit 124) |
| qemu_exit | **124** |
| timeout | **yes** (1200s) |
| autopilot_status | **failed** |
| guest_found | **false** |
| report_new | **false** |
| fleet session id | `fleet-qemu_rescue_developer_autopilot_20260602_202725` |
| rescue-agent session id | **none** |
| errors/findings | `serial_empty`, `qemu_timeout_124`, `guest_report_missing` |

## operator_smoke.log (Auszug)

- `head=9607b63` (vor Preflight-Guard)
- `PROFILE_GUARD_OK local_lab` — **kein** `DEVSERVER_PREFLIGHT_OK`
- Proxy `0.0.0.0:8001` → `127.0.0.1:8000`
- `{"status": "failed", "report_new": false, "guest_found": false}`

**Status:** `blocked` (Run nicht post-Preflight; Ergebnis failed)
