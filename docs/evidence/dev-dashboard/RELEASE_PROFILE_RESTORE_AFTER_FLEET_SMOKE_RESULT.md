# Release-Profil Restore — Ergebnis

**Stand:** 2026-06-02  
**Status:** **ok** (`release_restore_status=ok`)

## Phase-1-Kriterien (alle erfüllt)

| Kriterium | Ergebnis |
|-----------|----------|
| `install_profile=release` | **yes** |
| `profile_gate_status=green` | **yes** |
| `dev_control_enabled=false` | **yes** |
| `backend_runtime_path=/opt/setuphelfer/backend` | **yes** |
| `/api/dev-dashboard/status` → `PROFILE_ROUTE_BLOCKED` | **yes** (404, **expected_profile_block**) |
| `/api/fleet/sessions` → `PROFILE_ROUTE_BLOCKED` | **yes** (404, **expected_profile_block**) |
| `check-runtime-profile-deploy-gate.sh` Exit 0 | **yes** |
| `setuphelfer-backend.service` active | **yes** |

## Flags

| Flag | Wert |
|------|------|
| `release_restore_blocked_sudo_required` | **resolved** |
| `local_lab_open_after_smoke` | **false** |

## Historie

| Phase | Status |
|-------|--------|
| Cursor-Lauf (`9438901`) | **blocked** (`sudo`) |
| Operator-Restore + Ingest (`050d119`) | **ok** |

Evidence: `RELEASE_PROFILE_RESTORE_OPERATOR_INGEST.md`

## Legacy Deploy-Gate

`check-runtime-deploy-gate.sh` Exit **20** — informational unter `release`, kein Release-Restore-Fehler.
