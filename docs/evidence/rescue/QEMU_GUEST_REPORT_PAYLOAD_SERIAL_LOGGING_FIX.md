# QEMU Guest Report Payload — Serial Logging Fix

**Status:** implementiert

| Check | Wert |
|-------|------|
| neue Marker | **yes** |
| Secrets vermieden | **yes** (Payload-Summary nur run_id/session_id/node_id/report_type) |
| Response sichtbar | **yes** (gekürzt 2000 Zeichen) |
| Fehlerklasse sichtbar | **yes** (`SETUPHELFER_DEVSERVER_AGENT_SEND_FAILED class=...`) |

## Marker

- `SETUPHELFER_DEVSERVER_AGENT_SEND_START`
- `SETUPHELFER_DEVSERVER_AGENT_SEND_TARGET`
- `SETUPHELFER_DEVSERVER_AGENT_SEND_PAYLOAD_SUMMARY`
- `SETUPHELFER_DEVSERVER_AGENT_SEND_HTTP_STATUS`
- `SETUPHELFER_DEVSERVER_AGENT_SEND_RESPONSE_BODY`
- `SETUPHELFER_DEVSERVER_AGENT_SEND_OK` / `SETUPHELFER_DEVSERVER_AGENT_SEND_FAILED`

## Serial-JSON

Multi-Line: `BEGIN` / JSON / `END` (Parser aktualisiert). Kein JSON mehr in einer Zeile mit systemd-ANSI.

## Dateien

- `build/rescue/profiles/developer-qemu/.../setuphelfer-qemu-smoke-autopilot.sh`
- `scripts/rescue-live/parse-qemu-serial-smoke-result.py`
