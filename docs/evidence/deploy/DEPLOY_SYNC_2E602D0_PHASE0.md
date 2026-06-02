# Deploy-Sync 2e602d0 — Phase 0

**Stand:** 2026-06-02  
**Ziel-HEAD:** `2e602d0` (inkl. Vorgänger `00615d5`)

## Git (Workspace `/home/volker/piinstaller`)

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `2e602d0` |
| Workspace dirty | **ja** (~91 geänderte/untracked Einträge) |
| Deploy aus Workspace | **verboten** (rsync kopiert Arbeitsbaum) |

## Services (vor Deploy)

| Service | Status |
|---------|--------|
| `setuphelfer-backend.service` | active |

## Runtime (vor Deploy, readonly)

| Prüfung | Ergebnis |
|---------|----------|
| Legacy `check-runtime-deploy-gate.sh` | non-zero (dev-dashboard 404 in `release`) |
| `install_profile` (API) | `release` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `rescue_agent_router_status` | **fehlt** (`<missing>`) |
| `startup_diagnostics_status` | **fehlt** |
| `router_registry_summary` | **fehlt** |
| Deploy-Drift | **ja** — `/opt` ohne `rescue_agent/`, ohne `app_bootstrap/` |

## Entscheidung

Sauberer Deploy nur aus **detached Worktree** `2e602d0` (siehe `DEPLOY_SYNC_2E602D0_SOURCE_VERIFICATION.md`).
