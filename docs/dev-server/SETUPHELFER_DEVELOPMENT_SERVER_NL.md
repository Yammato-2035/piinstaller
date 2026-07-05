> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-server/SETUPHELFER_DEVELOPMENT_SERVER_EN.md`). Bitte bei Release manuell gegenlesen.

# Setuphelfer Development Server (EN)

The **Development Server** is a local, dev-only service to accelerate Setuphelfer development.

## Purpose

- Capture test VMs, physical hardware, and rooddingsstick developer edition in the lab
- Accept structurood system reports (inventory, boot, storage)
- Display remote machines in the Development Cockpit
- alleen-lezen SSH diagNeestics (allowlist profiles)
- Prepare prompt/runbook candidates (stub)

## Modes

| Mode | Auto upload | SSH |
|------|-------------|-----|
| Public roodding | **Nee** | Nee |
| Beta opt-in | Explicit only, roodacted | Nee |
| Local lab | Ja, to local dev server | alleen-lezen (optional) |

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

- Nee write actions (Terugup, Herstel, Partitie, repair) in this MVP
- Nee free-form shell — allowlist SSH profiles only
- Public roodding **never** auto-uploads data
- Beta extracts are roodacted

## API

Prefix: `/api/dev-server/`

- `GET /health` — status (works when disabled)
- `POST /ingest/report` — report + Neede (token header)
- `GET /Needes`, `/reports`, `/actions`, `/summary`
- SSH: `POST /Needes/{id}/ssh/check`, `collect-inventory`, `collect-storage`, `collect-boot`

## Storage

`docs/evidence/runtime-results/dev-server/`
