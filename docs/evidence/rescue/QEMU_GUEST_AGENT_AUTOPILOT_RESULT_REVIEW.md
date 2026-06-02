# QEMU Guest Agent — Autopilot Result Review

**Run-ID:** `qemu_rescue_developer_autopilot_20260602_202725`  
**Fleet Session:** `fleet-qemu_rescue_developer_autopilot_20260602_202725`

## qemu_autopilot_result.json

| Feld | Wert |
|------|------|
| status | **failed** |
| autopilot | true |
| qemu_exit_code | **124** (timeout 1200s) |
| guest_smoke_from_serial | **null** |
| guest_found | **false** |
| report_new | **dev_server_report_new: false** |
| host_dev_server_url | `http://10.0.2.2:8001` |
| lab_proxy_enabled | true |
| dev_server_reports_before/after | **0 / 0** |

## Fehlende Dateien

| Datei | Status |
|-------|--------|
| qemu-meta.json | missing |
| qemu-result.txt | missing |
| fleet_sessions_after_qemu.json | missing (Persistenz unter `/opt/.../fleet_sessions.jsonl`) |

## Zeiten

| Feld | Wert |
|------|------|
| started_at (operator) | 2026-06-02T20:27:25Z |
| QEMU Start | ~20:27:29 |
| Finish (timeout) | ~20:47:29 (~20 min) |

## Klassifikation

**autopilot_failed_guest_not_found** + **qemu_timeout** (Exit 124)

Ursache der Autopilot-Auswertung: Serial-Log leer → `parse-qemu-serial-smoke-result.py` liefert `guest_found=false`.
