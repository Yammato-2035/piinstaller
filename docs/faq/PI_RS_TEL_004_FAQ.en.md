# PI-RS-TEL-004 FAQ (EN)

## Why is 192.168.178.140 no longer the default?

The LAN proxy was a **lab setup** (developer laptop → local backend). Production now targets the **IONOS cloud server** `https://telemetrie.setuphelfer.de`.

## Why is changing the URL not enough?

The legacy payload (`rescue_boot_network_telemetry`, schema v1) does not match the cloud contract `telemetry.rescue.beta.v2`. Paths, schema, and auth differ.

## What is the new default?

| Setting | Value |
|---------|-------|
| Base URL | `https://telemetrie.setuphelfer.de` |
| Health | `/v1/telemetry/health` |
| Ingest | `/v1/telemetry/ingest` |
| Schema | `telemetry.rescue.beta.v2` |

## How do I enable legacy LAN?

```bash
SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE=legacy
SETUPHELFER_RESCUE_TELEMETRY_BASE_URL=http://192.168.178.140:8001
```

## Where do secrets live?

In operator **`network.env`** on USB (`SETUPHELFER_RESCUE_CONFIG/`) and an optional secret file — **never** in the git repo.

## When is data actually sent?

Only when all gates pass:

- `preview_only=true`, `production_ready=false`
- `SETUPHELFER_RESCUE_TELEMETRY_OPERATOR_CONSENT=explicit`
- Auth configured (HMAC key + secret file)
- `SETUPHELFER_RESCUE_TELEMETRY_CLOUD_SEND_ENABLED=1`

## Why no automatic cloud test?

Tests default to `external_calls=false`. Real HTTP only with an explicit flag — no secrets in CI.

## TLS error on the dev machine?

`SSL alert internal error` is classified as `tls_error` and documented. Operator checks certificate/SNI/reverse proxy (→ TEL-CLOUD-HEALTH-001).

## When does this reach the physical stick?

After **PI-RS-REPACK-001** (squashfs repack). Physical payload stays **1.10.0.12** until then.
