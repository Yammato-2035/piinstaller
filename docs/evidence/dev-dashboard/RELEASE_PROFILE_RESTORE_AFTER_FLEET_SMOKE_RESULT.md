# Release-Profil Restore — Ergebnis

**Stand:** 2026-06-02  
**Status:** **ok** (`release_restore_status=ok`)

## Operator-Restore

| Kriterium | Ergebnis |
|-----------|----------|
| `install_profile=release` | **yes** |
| `profile_gate_status=green` | **yes** |
| `dev_control_enabled=false` | **yes** |
| `backend_runtime_path=/opt/setuphelfer/backend` | **yes** |
| `/api/dev-dashboard/status` → `PROFILE_ROUTE_BLOCKED` | **yes** (404) |
| `/api/fleet/sessions` → `PROFILE_ROUTE_BLOCKED` | **yes** (404) |
| `check-runtime-profile-deploy-gate.sh` Exit 0 | **yes** |
| `setuphelfer-backend.service` active | **yes** |

## Historie

| Phase | Status |
|-------|--------|
| Cursor-Lauf | **blocked** (`sudo`) |
| Operator-Ingest | **ok** — siehe `RELEASE_PROFILE_RESTORE_OPERATOR_INGEST.md` |

## Legacy Deploy-Gate

`check-runtime-deploy-gate.sh` Exit **20** unter `release` — **informational**, kein Release-Restore-Fehler.
