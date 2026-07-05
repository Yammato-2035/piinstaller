# PI-RS-TEL-002 — Network-Gated Reachability + Offline Queue Preview

## Scope

Extends PI-RS-TEL-001 with profile-aware runtime gates, telemetry reachability checks, gated send-preview, and offline queue **preview only**.

**Not in scope:** production telemetry, auto-replay, workers, timers, real offline queue processing.

## Gates (send-preview order)

1. Install profile (`developer` / `local_lab` / `rescue_lab`)
2. Lab base URL configured
3. Secret configured
4. PII validator (PI-RS-TEL-001)
5. Reachability check (GET probe, no payload send)
6. Live send only if:
   - `allow_send_when_reachable=true` in request body
   - `SETUPHELPER_ENABLE_LIVE_LAB_TELEMETRY_TEST=1`
   - reachability = `reachable`

**Default:** `dry_run` — no network POST.

## API

| Method | Path | Release |
|--------|------|---------|
| `GET` | `/api/rescue/telemetry/lab/reachability` | 403 |
| `POST` | `/api/rescue/telemetry/lab/send-preview` | 403 |

## Offline queue preview

- Path: `docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/`
- `auto_replay_enabled`: always `false`
- No worker, no retry, no timer

## Profile-aware runtime gate

`scripts/check-profile-aware-runtime-gate.sh`  
Env: `SETUPHELPER_EXPECTED_PROFILE` (default: `release`)

## Next phase

**PI-RS-TEL-003** — Lab runtime profile deploy + manual live-lab send validation (no auto-deploy, no MSI hardware flow).
