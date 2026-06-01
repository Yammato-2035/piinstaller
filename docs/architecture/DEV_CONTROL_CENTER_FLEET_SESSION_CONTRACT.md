# Development Control Center — Fleet Session Contract (Phase 1)

**Version:** 1.7.3.0  
**Status:** Phase 1 — local lab only  
**Scope:** read-only UI + host state documentation (no control actions)

## Session types

| `session_type` | Beschreibung |
|----------------|--------------|
| `local_qemu_smoke` | `run-qemu-developer-iso-smoke.sh` |
| `local_agent_smoke` | Reserviert |
| `local_manual_lab` | Reserviert |

## Status values

`queued`, `starting`, `proxy_starting`, `proxy_ready`, `qemu_starting`, `booting`, `autopilot_waiting`, `guest_report_seen`, `serial_active`, `serial_empty`, `timeout_warning`, `timeout`, `failed`, `success`, `cancelled`, `unknown`

## Severity

`info` | `warning` | `error`

## Pflichtfelder (Session-Objekt)

```json
{
  "session_id": "fleet-<run_id>",
  "run_id": "<run_id>",
  "session_type": "local_qemu_smoke",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "started_at": "ISO-8601",
  "finished_at": null,
  "status": "starting",
  "severity": "info",
  "label": "QEMU Developer ISO Smoke",
  "host": {
    "hostname": "...",
    "user": "...",
    "has_kvm": true,
    "kvm_enabled": true
  },
  "qemu": {
    "pid": null,
    "iso_path": "build/rescue/.../binary.hybrid.iso",
    "proxy_port": 8001,
    "timeout_seconds": 900,
    "acceleration": "kvm|tcg|unknown",
    "exit_code": null
  },
  "guest": {
    "report_seen": false,
    "guest_node_id": null,
    "guest_smoke_status": null,
    "dev_server_report_new": false
  },
  "serial": {
    "path": ".../qemu-serial.log",
    "exists": false,
    "size_bytes": 0,
    "last_size_change_at": null
  },
  "heartbeat": {
    "last_heartbeat_at": "ISO-8601",
    "age_seconds": 0,
    "healthy": true,
    "stalled": false,
    "stall_reason": ""
  },
  "evidence_paths": ["docs/evidence/runtime-results/rescue/qemu/<run_id>"],
  "findings": [],
  "errors": []
}
```

## API (keine Control-Endpunkte)

| Methode | Pfad | Zweck |
|---------|------|--------|
| GET | `/api/fleet/sessions` | Liste |
| GET | `/api/fleet/sessions/summary` | Aggregation |
| GET | `/api/fleet/sessions/{session_id}` | Detail |
| POST | `/api/fleet/sessions` | Create (Wrapper) |
| POST | `/api/fleet/sessions/{id}/heartbeat` | Heartbeat |
| POST | `/api/fleet/sessions/{id}/finish` | Abschluss |

**Verboten:** `/execute`, `/start`, `/stop`, `/revive`, `/control`, `/ssh`, `/remote`

## Response codes

`FLEET_SESSION_CREATED`, `FLEET_SESSION_UPDATED`, `FLEET_SESSION_HEARTBEAT_OK`, `FLEET_SESSION_FINISHED`, `FLEET_SESSION_LIST_OK`, `FLEET_SESSION_NOT_FOUND`, `FLEET_SESSION_BLOCKED_INVALID_PAYLOAD`

## Stale / Hang rules

| Bedingung | Wirkung |
|-----------|---------|
| Heartbeat > 60 s | `severity=warning`, Finding `heartbeat_delayed` |
| Heartbeat > 180 s (running) | `status=timeout_warning` |
| Heartbeat > timeout_seconds + 60 | `status=timeout` |
| `qemu_exit_code=124` on finish | `status=timeout`, Finding `qemu_timeout_124` |
| Serial 0 B nach ≥120 s Boot | `status=serial_empty`, Finding `serial_empty` (kein Auto-Fail) |
| Kein Gast-Report bei Ende | Finding `guest_report_missing` |

## Persistenz

- `docs/evidence/runtime-results/dev-dashboard/fleet_sessions.jsonl`
- `docs/evidence/runtime-results/dev-dashboard/fleet_sessions_latest.json`

## Regeln

- Session ist **hostseitig** sichtbar ohne Gast-Report.
- Gast-Report **ergänzt** die Session, ersetzt sie nicht.
- Keine Secrets, keine Tokens in Payloads.
- Produktion/Schule/Remote-Control: **out of scope** Phase 1.
