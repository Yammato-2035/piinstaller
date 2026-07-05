# PI-RS-TEL-001 Summary

## Status

| Item | Value |
|------|-------|
| Phase | PI-RS-TEL-001 |
| Workspace | `/home/volker/piinstaller` |
| Branch | `main` |
| Production ready | **false** |
| Live lab test | **not performed** (no `SETUPHELPER_ENABLE_LIVE_LAB_TELEMETRY_TEST=1`) |
| Runtime gate | `runtime_gate_blocked_static_or_unit_only` (release profile, DCC 404) |

## Delivered

- Synthetic rescue lab payload model with PII validator
- HMAC-v2 signing (TEL-012 compatible headers and message format)
- HTTP client with structured status mapping (202/401/403/409)
- Dev/lab-only API: `POST /api/rescue/telemetry/lab/send-preview`
- DCC compact status + Rescue panel with one-shot „Lab-Send testen“
- Evidence export (redacted)
- Safety gate script integrated in `run-tests.sh`

## TEL-012 reference

See `docs/evidence/PI_RS_TEL_001_TELEMETRY_SERVER_CONTRACT_REFERENCE.md`

## Next phase

**PI-RS-TEL-002** — network-gated reachability + offline queue preview (roadmap only).
