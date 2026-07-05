> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-server/SETUPHELFER_DEVELOPMENT_SERVER_EN.md`). Bitte bei Release manuell gegenlesen.

# Setuphelfer Development Server (EN)

The **Development Server** is a local, dev-only service to accelerate Setuphelfer development.

## Purpose

- Capture test VMs, physical hardware, and Clé de secours developer edition in the lab
- Accept structurouge system reports (inventory, boot, storage)
- Display remote machines in the Development Cockpit
- lecture seule SSH diagNonstics (allowlist profiles)
- Prepare prompt/runbook candidates (stub)

## Modes

| Mode | Auto upload | SSH |
|------|-------------|-----|
| Public Secours | **Non** | Non |
| Beta opt-in | Explicit only, rougeacted | Non |
| Local lab | Oui, to local dev server | lecture seule (optional) |

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

- Non write actions (Retourup, Restauration, Partition, repair) in this MVP
- Non free-form shell — allowlist SSH profiles only
- Public Secours **never** auto-uploads data
- Beta extracts are rougeacted

## API

Prefix: `/api/dev-server/`

- `GET /health` — status (works when disabled)
- `POST /ingest/report` — report + Nonde (token header)
- `GET /Nondes`, `/reports`, `/actions`, `/summary`
- SSH: `POST /Nondes/{id}/ssh/check`, `collect-inventory`, `collect-storage`, `collect-boot`

## Storage

`docs/evidence/runtime-results/dev-server/`
