# Rescue Telemetry — Operator `network.env`

**Do not commit** real `network.env` files. Use `network.env.example` on USB only.

## Locations (stick runtime)

The rescue shell loads the first readable file from:

1. `/run/setuphelfer-rescue/network.env`
2. `/etc/setuphelfer-rescue/network.env`
3. `/media/*/SETUPHELFER_CONFIG/network.env`
4. `/media/*/SETUPHELFER_RESCUE_CONFIG/network.env`

## Cloud production example

```bash
# Copy to SETUPHELFER_RESCUE_CONFIG/network.env on USB — never commit secrets.
SETUPHELFER_RESCUE_TELEMETRY_BASE_URL=https://telemetrie.setuphelfer.de
SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE=cloud
SETUPHELFER_RESCUE_TELEMETRY_AUTH_MODE=hmac
SETUPHELFER_RESCUE_TELEMETRY_KEY_ID=<operator-provided>
SETUPHELFER_RESCUE_TELEMETRY_SECRET_FILE=/run/setuphelfer/telemetry_secret
SETUPHELFER_RESCUE_TELEMETRY_OPERATOR_CONSENT=explicit
# Cloud send remains disabled until explicitly enabled:
# SETUPHELFER_RESCUE_TELEMETRY_CLOUD_SEND_ENABLED=1
```

## Legacy LAN lab override

```bash
SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE=legacy
SETUPHELFER_RESCUE_TELEMETRY_BASE_URL=http://192.168.178.140:8001
```

Requires `start-rescue-telemetry-lan-proxy.sh` on the developer laptop.

## Rules

| Rule | Detail |
|------|--------|
| No secrets in repo | Secret file path only; content on stick/runtime |
| No default secret | Missing secret → send blocked |
| Operator consent | `SETUPHELFER_RESCUE_TELEMETRY_OPERATOR_CONSENT=explicit` required |
| Preview only | `production_ready=false` enforced in code |
| External probes | `SETUPHELFER_RESCUE_TELEMETRY_EXTERNAL_CALLS=1` for live health checks |

## Related

- `config/rescue_telemetry_endpoints.json`
- `docs/contracts/PI_RS_TEL_004_RESCUE_TELEMETRY_BETA_V2_CONTRACT.md`
- `backend/core/rescue_telemetry_auth_gate.py`
