# Setuphelfer Development Server (EN)

The **Development Server** is a local, dev-only service to accelerate Setuphelfer development.

## Purpose

- Capture test VMs, physical hardware, and rescue stick developer edition in the lab
- Accept structured system reports (inventory, boot, storage)
- Display remote machines in the Development Cockpit
- Read-only SSH diagnostics (allowlist profiles)
- Prepare prompt/runbook candidates (stub)

## Modes

| Mode | Auto upload | SSH |
|------|-------------|-----|
| Public rescue | **No** | No |
| Beta opt-in | Explicit only, redacted | No |
| Local lab | Yes, to local dev server | Read-only (optional) |

## Enable locally

```bash
export SETUPHELFER_DEV_SERVER_ENABLED=true
export SETUPHELFER_DEV_SERVER_MODE=local_lab
export SETUPHELFER_DEV_SERVER_TOKEN=your-local-token
# optional:
export SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH=true
```

See `.env.example.devserver` and `docs/runbooks/DEV_SERVER_LOCAL_LAB_SETUP_EN.md`.

## Safety

- No write actions (backup, restore, partition, repair) in this MVP
- No free-form shell — allowlist SSH profiles only
- Public rescue **never** auto-uploads data
- Beta extracts are redacted

## API

Prefix: `/api/dev-server/`

- `GET /health` — status (works when disabled)
- `POST /ingest/report` — report + node (token header)
- `GET /nodes`, `/reports`, `/actions`, `/summary`
- SSH: `POST /nodes/{id}/ssh/check`, `collect-inventory`, `collect-storage`, `collect-boot`

## Storage

`docs/evidence/runtime-results/dev-server/`
