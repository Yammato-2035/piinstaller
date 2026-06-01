# Fleet Session — QEMU Finish Telemetry Fix

**Stand:** 2026-06-01 · **Bezug:** Analyse `081222`

## Problem

Nach QEMU-Smoke `081222`:

| Feld | Evidence / Wrapper | Fleet API `latest.json` |
|------|-------------------|-------------------------|
| `qemu.exit_code` | 124 (Autopilot-JSON) | `null` |
| `serial.path` | Datei unter Evidence-Dir | `""` |
| `serial.exists` | Datei vorhanden | `false` |
| `serial.size_bytes` | 0 | 0 |
| `host.kvm_enabled` | KVM im Skript | `false` |
| `qemu.acceleration` | `kvm` | `unknown` |

Finish-Payload aus Wrapper war unvollständig; Heartbeat-Stale-Regeln setzten teils `timeout` ohne Exit-Code.

## Fix (Wrapper, kein Backend-Breaking-Change)

`fleet_session_finish_payload` ergänzt:

```json
{
  "qemu_exit_code": 124,
  "qemu": { "exit_code": 124, "acceleration": "kvm" },
  "serial": { "path": "/…/qemu-serial.log", "exists": true, "size_bytes": 0 },
  "host": { "kvm_enabled": true, "has_kvm": true },
  "findings": ["serial_empty", "classification_hint_serial_empty_boot_unknown", "qemu_timeout_124", …]
}
```

`run-qemu-developer-iso-smoke.sh` setzt vor Finish:

- `FLEET_SERIAL_PATH`, `FLEET_SERIAL_EXISTS`, `FLEET_ACCELERATION`, `FLEET_KVM_ENABLED`, `FLEET_HAS_KVM`
- `findings_json` bei `serial_size=0`

## Verifikation

- Statisch: `scripts/tests/test_rescue_developer_serial_cmdline_v1.sh`
- Live: beim **nächsten** QEMU-Lauf nach ISO-Rebuild + Backend-Deploy des Wrapper-Stands

## Guardrails

- Keine Control-Routen, kein QEMU in diesem Auftrag.
