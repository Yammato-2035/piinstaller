# PI-RS-TEL-002 FAQ (EN)

## What is new vs PI-RS-TEL-001?

Reachability checks, profile-aware runtime gate, and offline queue **preview** — no auto-replay.

## Does reachability send telemetry?

**No.** HTTP probe to the lab server only, no payload.

## When is live send performed?

Only with explicit `allow_send_when_reachable=true` **and** `SETUPHELPER_ENABLE_LIVE_LAB_TELEMETRY_TEST=1` **and** a reachable endpoint.

## Is there a real offline queue?

**No.** Redacted preview files only under `docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/`.

## Release profile?

Lab routes return HTTP 403 `feature_disabled`. DCC 404 in release is expected.

## Next phase?

**PI-RS-TEL-003** — manual live-lab validation after profile deploy.
