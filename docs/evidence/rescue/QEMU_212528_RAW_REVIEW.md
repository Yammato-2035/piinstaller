# QEMU 212528 — Raw Evidence Review

**Run:** `qemu_rescue_developer_autopilot_20260603_212528`  
**Operator-Log:** `operator_smoke.log` (head `e7f0bc2`)

## Autopilot Result

| Feld | Wert |
|------|------|
| `qemu_autopilot_result` vorhanden | **yes** |
| `status` | `failed` |
| `guest_found` | **false** (Wrapper-Summary) |
| `report_new` | **false** |
| `qemu_exit_code` | **124** (timeout) |
| `dev_server_reports_before/after` | 0 / 0 |

## Serial

| Feld | Wert |
|------|------|
| serial vorhanden | **yes** |
| serial size | **133 260 B** |
| bootloader_seen | **yes** (ISOLINUX 6.04) |
| kernel_seen | **yes** (`Linux version 6.1.0-49-amd64`, `console=ttyS0`) |
| systemd_seen | **yes** (`Reached target multi-user.target`) |
| autopilot_seen | **yes** (`SETUPHELFER_AUTOPILOT_START run_id=qemu_smoke_20260603_212538`) |

## Fehler-Marker (Serial)

| Marker | Vorhanden |
|--------|-----------|
| `ModuleNotFoundError` | **no** |
| `Invalid Host header` | **no** |
| `agent_send_failed` | **yes** (`SETUPHELFER_DEVSERVER_AGENT_ERROR:agent_send_failed`) |
| Guest-Report gesendet (Host) | **no** |

## Klassifikation (Serial)

**`autopilot_report_send_failed_new_reason`**

Autopilot lief bis Report-Versuch; Import- und Host-Header-Fehler aus Run `111427` **nicht** mehr sichtbar. Neuer Blocker: Agent-Send schlägt fehl ohne ModuleNotFound/Invalid-Host.

Sekundär: **`qemu_timeout_after_autopilot`** — VM lief bis Timeout 124 nach frühem Autopilot-Ende.

## Artefakte

- `qemu_212528_serial_extract_latest.log`
- `qemu_212528_serial_markers_latest.log`
- `qemu_212528_autopilot_result_latest.json`
