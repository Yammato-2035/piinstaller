# PI-RS-TEL-004 — Summary

**Sprint:** PI-RS-TEL-004
**Date:** 2026-07-10
**Workspace version:** 1.9.19.5
**Physical stick payload (unchanged):** 1.10.0.12

## WIP classification

| Class | Files | Action |
|-------|-------|--------|
| A — Cloud endpoint WIP | `config/rescue_telemetry_endpoints.json`, `rescue_telemetry_endpoints.py`, shell defaults, lab reachability | **Adopted** into PI-RS-TEL-004 |
| B — MSI retest WIP | — | Not present |
| C — Runtime queue artefacts | — | Not adopted |
| D — Build artefacts | `controlled_iso_build_latest_summary.json`, `update-fat32-esp-live-payload.sh` | **Reverted** (out of scope) |

## Deliverables

- Central endpoint config (`config/rescue_telemetry_endpoints.json`)
- Payload v2 preview builder (`backend/core/rescue_telemetry_payload_v2.py`)
- Auth gate (`backend/core/rescue_telemetry_auth_gate.py`)
- Cloud reachability gate (`backend/core/rescue_telemetry_cloud_reachability.py`)
- 7 test modules + smoke script
- Contract/docs/FAQ

## Not done (by design)

- Repack / USB write
- MSI boot retest
- Production cloud send
- Real TLS curl in automated tests

## TLS note

Dev machine `curl` → `telemetrie.setuphelfer.de`: **SSL alert internal error** (documented, classified as `tls_error`).

## Next step

**PI-RS-REPACK-001** — embed v2 into squashfs for MSI retest.
