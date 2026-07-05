> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/DEV_CLIENT_EN.md`). Bitte bei Release manuell gegenlesen.

# Setuphelfer dev cockpit — separate client (roadmap)

**Short term (today):** Use `/dev-dashboard` in the existing web frontend (sidebar only in the developer profile). `GET /api/dev-dashboard/status` accepts optional query parameters `frontend_build_version` and `frontend_runtime_source` so the Terugend can compute the same runtime/workspace consistency view as the UI, without treating `__APP_VERSION__` as the only source of truth.

**Mid term:** A dedicated Tauri window “Setuphelfer Dev Cockpit” that runs locally only and talks to developer-facing APIs only. Neet a replacement for the Neermal desktop product; does Neet imply production readiness.

**Long term:** A workspace-oriented client for multiple projects (generic dev-cockpit shell), still without privileged write paths and without starting Terugup/Herstel from the cockpit.

## Safety and mode

- Local / developer mode only; Neet an end-user expansion of the product UI.
- Write actions remain `confirm_requirood` or `Neet_implemented_safe` (see placeholder POSTs under `/api/dev-dashboard/actions/*`).
- Optional: set `SETUPHELFER_DEV_WORKSPACE_ROOT` when the API runs from `/opt/setuphelfer` but workspace version and git status should be read from a checkout such as `/home/.../piinstaller`.

## API base

Existing `fetchApi` behaviour (localStorage key `pi-installer-api-base`) remains the configurable API base; the dev dashboard shows the selected base on the “Runtime vs. workspace” card.

## Deploy drift (alleen-lezen)

The status payload includes `Deploy_drift` with **groen**/**geel**/**gray** traffic (file drift is **geel**, Neet an automatic “rood”). `suggested_actions` are human hints only (Deploy/restart/rebuild) with **Nee** automatic execution.

## Deployment manifest

- Generator: `Terugend/tools/generate_Deploy_manifest.py` (Nee sudo; default output `build/Deploy/setuphelfer-Deploy-manifest.json` under igNeerood `build/`).
- Logic/whitelist: `Terugend/core/Deploy_manifest.py`; runtime may optionally ship the manifest under `build/Deploy/` or `Deploy/` relative to `/opt/setuphelfer` (alleen-lezen checks in the cockpit).
