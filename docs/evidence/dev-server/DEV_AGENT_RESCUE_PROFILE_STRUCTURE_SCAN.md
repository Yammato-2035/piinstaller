# Dev Agent — Rescue Profile Structure Scan

**Date:** 2026-05-30
**HEAD:** 0748492+

## Findings

| Area | Path | Notes |
|------|------|-------|
| Live-build tree | `build/rescue/live-build/setuphelfer-rescue-live/` | Existing ISO build workspace; **not modified** in this run |
| Debian-live config | `build/rescue/debian-live/` | Package lists, manifests |
| Agent systemd template (host) | `packaging/systemd/setuphelfer-dev-agent.service` | Default **disabled**, public_rescue |
| **New developer profile** | `build/rescue/profiles/developer/` | Profile-only, no build |
| **New public guard profile** | `build/rescue/profiles/public/` | Explicit AUTO_UPLOAD=false |
| Dev agent module | `backend/devserver_agent/` | Collector, client, CLI |
| Dev server | `backend/devserver/` | Ingest API (runtime green) |

## Integration point chosen

**`build/rescue/profiles/developer/`** — isolated profile bundle (manifest, env, systemd) that a future Rescue Developer ISO build can copy into the live system without touching the public live-build tree.

Rationale:
- Avoids mixing with in-progress rescue ISO WIP under `live-build/`
- Clear separation public vs developer
- Validatable without `lb build`

## Public profile

Minimal `build/rescue/profiles/public/` with safe defaults. Public live-build does **not** yet reference agent env — guard enforced by profile + tests.

## Risks

- Future live-build hook must **select profile** explicitly (developer vs public)
- EnvironmentFile path on live system may differ (`/etc/setuphelfer/` vs `/opt/setuphelfer/config/`)
- No token in profile — operator must set locally if token required later

## Open questions

- When to wire profile into `prepare-controlled-live-build-tree.sh` (next prompt: dry-build)
- Timer for periodic agent send (optional, default off)
