# QEMU Guest Agent After Registry — Raw Review

**Datum:** 2026-06-03  
**run_id:** `qemu_rescue_developer_autopilot_20260603_111427`

## Autopilot-Ergebnis (Host)

| Feld | Wert |
|------|------|
| `qemu_autopilot_result.json` vorhanden | **yes** |
| `status` | **failed** |
| `guest_found` | **false** (Host-Watcher) |
| `report_new` | **false** |
| `qemu_exit_code` | **124** (timeout 1200s) |
| `dev_server_reports_before/after` | 0 / 0 |

Artefakt: `qemu_guest_agent_after_registry_autopilot_result_latest.json`

## Serial

| Feld | Wert |
|------|------|
| `qemu-serial.log` vorhanden | **yes** |
| Größe | **135 299** Bytes |
| Bootloader-Marker (ISOLINUX) | **yes** |
| Kernel-Marker (`Linux version`) | **yes** |
| systemd-Marker | **yes** (`Reached target multi-user.target`) |
| SetupHelfer/Autopilot-Marker | **yes** |

### Entscheidende Serial-Zeilen (~Zeile 1084–1100)

```
Starting setuphelfer-qemu-smoke-autopilot.service ...
SETUPHELFER_AUTOPILOT_START run_id=qemu_smoke_20260603_111445
SETUPHELFER_DEVSERVER_AGENT_REPORT_ATTEMPT
SETUPHELFER_DEVSERVER_AGENT_ERROR:agent_send_failed
host_health_raw: "Invalid Host header"
agent_send_raw: ModuleNotFoundError: No module named 'devserver_agent'
SETUPHELFER_QEMU_SMOKE_RESULT_JSON_BEGIN {... status: review_required, agent_send_ok: false ...}
Finished setuphelfer-qemu-smoke-autopilot.service
```

Autopilot **lief und beendete sich** — danach lief QEMU bis Timeout (journald-Spam auf Serial).

Artefakte:

- `qemu_guest_agent_after_registry_serial_extract_latest.log`
- `qemu_guest_agent_after_registry_serial_markers_latest.log`
- `qemu_guest_agent_after_registry_run_files_latest.log`

## Klassifikation (Serial-Pipeline)

**autopilot_seen_no_report** (Autopilot gestartet, kein Devserver-Report am Host)

Nicht zutreffend: `serial_empty`, `bootloader_seen_only`, `kernel_seen_no_systemd`, `systemd_seen_no_autopilot`.
