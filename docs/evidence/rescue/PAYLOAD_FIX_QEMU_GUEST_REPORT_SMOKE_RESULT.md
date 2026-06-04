# Payload Fix — QEMU Guest Report Smoke

**Status:** `blocked`

| Feld | Wert |
|------|------|
| `qemu_smoke_exit` | **nicht ausgeführt** |
| `run_id` | — |
| Grund | Phase 8 nicht grün; `qemu-guest-agent-smoke-operator.sh` erfordert `sudo` + `local_lab` + frisches ISO |

## Vorheriger Referenzlauf

`qemu_rescue_developer_autopilot_20260603_212528` — `agent_send_failed`, keine SEND_HTTP_STATUS-Marker.

## Nach Fix-Rebuild erwartet

Serial muss zeigen: `SEND_TARGET`, `SEND_HTTP_STATUS`, `SEND_RESPONSE_BODY`, `SEND_OK` oder `SEND_FAILED` mit Klasse.
