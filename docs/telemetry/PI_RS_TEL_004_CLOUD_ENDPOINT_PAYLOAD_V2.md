# PI-RS-TEL-004 — Cloud Endpoint + Payload v2

**Version:** 1.9.19.5
**Physical stick payload (unchanged):** 1.10.0.12
**Repack:** deferred → PI-RS-REPACK-001

## Summary

PI-RS-TEL-004 moves the **default telemetry target** from the deprecated LAN proxy (`192.168.178.140:8001`) to the IONOS cloud server `https://telemetrie.setuphelfer.de` and introduces a **preview payload builder** for `telemetry.rescue.beta.v2`.

URL changes alone are insufficient because:

| Aspect | Legacy v1 | Cloud beta.v2 |
|--------|-----------|---------------|
| Schema | `rescue_boot_network_telemetry` | `telemetry.rescue.beta.v2` |
| Paths | `/api/rescue/telemetry/*` | `/v1/telemetry/*` |
| Auth | LAN proxy allowlist | HMAC/API key via operator env |
| Send mode | Local backend ingest | Gated cloud ingest |

## Configuration

**Canonical:** `config/rescue_telemetry_endpoints.json`

```json
{
  "default_profile": "cloud",
  "profiles": {
    "cloud": { "base_url": "https://telemetrie.setuphelfer.de", ... },
    "legacy_lan_lab": { "legacy": true, ... }
  }
}
```

**Shell defaults:** `scripts/rescue-live/image/setuphelfer-rescue-common.sh`

- `SETUPHELFER_RESCUE_TELEMETRY_BASE_URL=https://telemetrie.setuphelfer.de`
- `SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE=cloud`

## Safety gates

| Gate | Default |
|------|---------|
| `production_ready` | `false` |
| `preview_only` | `true` |
| `external_calls` | `false` |
| `cloud_send_requires_operator_consent` | `true` |

Cloud health probes require `SETUPHELFER_RESCUE_TELEMETRY_EXTERNAL_CALLS=1`.

## TLS observation (dev machine)

From the development workstation, `curl` against `telemetrie.setuphelfer.de` reported **TLS alert internal error** (OpenSSL). This is classified as `tls_error` in `rescue_telemetry_cloud_reachability.py` and documented here — not ignored.

Operator verification (manual, no secrets):

```bash
curl -v https://telemetrie.setuphelfer.de/v1/telemetry/health
```

Do **not** guess server IPs or send ingest without operator credentials.

## Next step

**PI-RS-REPACK-001** — embed v2 payload builder + cloud defaults into squashfs, then MSI retest.

If TLS persists: **TEL-CLOUD-HEALTH-001** — IONOS reverse proxy / certificate / SNI check.
