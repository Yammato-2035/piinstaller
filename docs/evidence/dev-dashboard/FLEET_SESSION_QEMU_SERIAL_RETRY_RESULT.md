# Fleet Session — QEMU Serial Visibility Retry

**Stand:** 2026-06-01
**SESSION_ID:** `fleet-qemu_rescue_developer_serial_20260601_160824`
**RUN_ID:** `qemu_rescue_developer_serial_20260601_160824`

## Fleet-API (`GET /api/fleet/sessions/{session_id}`)

| Feld | Wert |
|------|------|
| `status` | `timeout_warning` |
| `severity` | `warning` |
| `findings` | `heartbeat_delayed`, `timeout_warning` |
| `finished_at` | **null** (Finish nicht vollständig in API-Snapshot) |
| `serial.exists` | false |
| `serial.size_bytes` | 0 |
| `serial.path` | `""` (leer im Snapshot) |
| `qemu.exit_code` | null |
| `qemu.acceleration` | `unknown` |
| `host.kvm_enabled` | false (Snapshot; Skript meldete KVM aktiv) |
| `guest.report_seen` | false |
| `guest.dev_server_report_new` | false |

## Diagnostic Export

- **Verfügbar:** yes (`/api/dev-diagnostics/qemu-smokes/{run_id}/export`)
- **classification.primary:** `serial_empty_boot_unknown`
- **secondary:** `agent_not_observed`, `network_not_observed`, `devserver_ingest_missing`

## Autopilot JSON (Lauf-Evidence)

```json
{
  "status": "failed",
  "qemu_exit_code": 124,
  "dev_server_report_new": false,
  "autopilot": true,
  "manual_guest_input_required": false
}
```

## Bewertung

Serial-Sichtbarkeit über Fleet/Diagnostics konsistent **leer**. Fleet-Session-Telemetrie sollte im Folgefix `serial.path`, `serial.size_bytes` und `qemu.exit_code` nach Laufende setzen (Finish-Payload).

## Nächster Schritt

`FIX_QEMU_SERIAL_DEVICE_OR_BOOTLOADER_OUTPUT_CAPTURE` — kein erneuter Smoke ohne Fix.
