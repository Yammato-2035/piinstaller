# PI-RS-TEL-001 FAQ (EN)

## What does PI-RS-TEL-001 do?

First **lab-only** send flow for synthetic rescue-stick telemetry from the piinstaller workspace to the private telemetry server (TEL-012).

## Does it send real host data?

**No.** Only synthetic preview payloads — no MAC, IP, hostname, serial numbers, raw logs, or secrets.

## When is data sent?

Only on explicit `POST /api/rescue/telemetry/lab/send-preview` in a lab/dev install profile. No automatic send on startup.

## What if the secret is missing?

`blocked_missing_secret` — no network send, clear operator message.

## Is this production-ready?

**No.** `production_ready=false` everywhere. HMAC success means lab acceptance only, not production release.

## Next phase?

**PI-RS-TEL-002** — network-gated reachability + offline queue preview (no real replay queue yet).
