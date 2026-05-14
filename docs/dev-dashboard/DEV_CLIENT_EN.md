# Setuphelfer dev cockpit — separate client (roadmap)

**Short term (today):** Use `/dev-dashboard` in the existing web frontend (sidebar only in the developer profile). `GET /api/dev-dashboard/status` accepts optional query parameters `frontend_build_version` and `frontend_runtime_source` so the backend can compute the same runtime/workspace consistency view as the UI, without treating `__APP_VERSION__` as the only source of truth.

**Mid term:** A dedicated Tauri window “Setuphelfer Dev Cockpit” that runs locally only and talks to developer-facing APIs only. Not a replacement for the normal desktop product; does not imply production readiness.

**Long term:** A workspace-oriented client for multiple projects (generic dev-cockpit shell), still without privileged write paths and without starting backup/restore from the cockpit.

## Safety and mode

- Local / developer mode only; not an end-user expansion of the product UI.
- Write actions remain `confirm_required` or `not_implemented_safe` (see placeholder POSTs under `/api/dev-dashboard/actions/*`).
- Optional: set `SETUPHELFER_DEV_WORKSPACE_ROOT` when the API runs from `/opt/setuphelfer` but workspace version and git status should be read from a checkout such as `/home/.../piinstaller`.

## API base

Existing `fetchApi` behaviour (localStorage key `pi-installer-api-base`) remains the configurable API base; the dev dashboard shows the selected base on the “Runtime vs. workspace” card.

## Deploy drift (read-only)

The status payload includes `deploy_drift` with **green**/**yellow**/**gray** traffic (file drift is **yellow**, not an automatic “red”). `suggested_actions` are human hints only (deploy/restart/rebuild) with **no** automatic execution.
