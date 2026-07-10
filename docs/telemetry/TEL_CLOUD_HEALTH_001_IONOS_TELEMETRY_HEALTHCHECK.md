# TEL-CLOUD-HEALTH-001 — IONOS Telemetry Healthcheck

**Sprint:** TEL-CLOUD-HEALTH-001
**Date:** 2026-07-10
**Probe host:** Dev workstation (`/home/volker/piinstaller`)
**Repo HEAD at probe:** `9cf66f618f79a37e1a3cf4e07a133c2ff9cb01d0`

## Endpoint

| Field | Value |
|-------|-------|
| Base URL | `https://telemetrie.setuphelfer.de` |
| Health | `/v1/telemetry/health` |
| Full health URL | `https://telemetrie.setuphelfer.de/v1/telemetry/health` |
| Ingest | `/v1/telemetry/ingest` |
| **Ingest tested** | **no** |
| Secrets/API keys used | **no** |

## Result

**Classification:** `tls_error`

## Evidence summary

### DNS — OK

| Record | Value |
|--------|-------|
| A | `217.160.0.254` |
| AAAA | `2001:8d8:100f:f000::200` |
| getent | resolves (IPv6 first) |

See: `docs/evidence/tel_cloud_health_001_ionos_telemetry_healthcheck/dns-check.txt`

### TLS/SNI — FAIL (`tls_error`)

- TCP connect to `:443` succeeds (IPv4 and IPv6).
- TLS handshake fails immediately after ClientHello.
- Server alert: **internal error (alert 80)**.
- **No peer certificate** delivered (`no peer certificate available`).
- OpenSSL/curl: `SSL routines::tlsv1 alert internal error` (OpenSSL 3.0.13).

Interpretation: The host accepts TCP but cannot complete TLS for SNI `telemetrie.setuphelfer.de`. Typical causes on Plesk/IONOS:

1. Subdomain not bound to a certificate on port 443.
2. Reverse proxy / vhost missing or misconfigured for this hostname.
3. Telemetry app not listening behind the proxy (TLS terminates before app routing).

See: `tls-sni-check.txt`, `curl-health-check.txt`, `curl-ipv4-ipv6-check.txt`

### HTTP Health — not reached

- `http_code=000` (TLS failure before HTTP).
- No response body.
- Same failure on **IPv4** (`217.160.0.254`) and **IPv6** (`2001:8d8:100f:f000::200`).

### IPv4 vs IPv6

Both fail identically at TLS — not an IPv6-only routing issue.

## Interpretation

DNS and L4 reachability are fine. **L7/TLS is broken** from the dev workstation. PI-RS-TEL-004 cloud defaults are correct in config, but the **live IONOS endpoint is not yet usable** for health checks or ingest.

This matches the earlier PI-RS-TEL-004 observation (`SSL alert internal error`).

## Required fix (TEL-CLOUD-FIX-001)

Operator/server-side (Plesk/IONOS), no repo auto-remediation:

1. Verify Plesk subdomain `telemetrie.setuphelfer.de` exists with valid Let's Encrypt (or other) certificate.
2. Confirm reverse proxy forwards to telemetry app (e.g. `127.0.0.1:8101` per deployment docs).
3. Re-test manually:
   ```bash
   curl -v https://telemetrie.setuphelfer.de/v1/telemetry/health
   openssl s_client -connect telemetrie.setuphelfer.de:443 -servername telemetrie.setuphelfer.de </dev/null
   ```
4. Optional: test `/health` alias if Plesk maps root health differently.

Reference: `docs/deploy/TELEMETRY_PLESK_REVERSE_PROXY_DE.md`

## Repack decision

**`repack_allowed_with_cloud_send_disabled`**

Rationale:

- SquashFS repack (PI-RS-REPACK-001) can proceed to embed v2 payload + cloud URL defaults.
- Cloud send remains gated (`CLOUD_SEND_ENABLED=1`, operator consent, auth) — telemetry will spool offline until TLS/health is fixed.
- **Do not** enable production cloud send or MSI cloud-send validation until classification becomes `health_ok`.

Alternative if operator prefers strict sequencing: defer repack until `health_ok` (`repack_blocked_until_cloud_health_ok`).

## Runtime artifact cleanup

| Item | Status |
|------|--------|
| Backup | `/home/volker/setuphelfer-backups/tel-cloud-health-001-runtime-artifacts-20260710-201342` |
| Untracked queue items removed | yes |
| Modified evidence restored from HEAD | yes |
| Working tree before commit | clean |

## Next step

1. **TEL-CLOUD-FIX-001** — Plesk TLS certificate + reverse proxy for `telemetrie.setuphelfer.de`
2. Re-run health probe after server fix
3. Then **PI-RS-REPACK-001** (with cloud send still gated until `health_ok`)
