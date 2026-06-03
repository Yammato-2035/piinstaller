# Backend Down After Release Restart — Release Gate Result (Phase 5)

**Datum:** 2026-06-03  
**HEAD:** `cce563b`

## Profile Gate

```
profile_gate: OK
check-runtime-profile-deploy-gate: OK (profile-aware)
PROFILE_GATE_EXIT=0
```

Log: `backend_down_after_release_restart_profile_gate_latest.log`

## Legacy Gate

```
LEGACY_GATE_EXIT=20
```

Erwartet unter **release** (dev-dashboard 404 informational).  
Log: `backend_down_after_release_restart_legacy_gate_latest.log`

## `/api/version` (Auszug)

| Feld | Wert |
|------|------|
| `install_profile` | `release` |
| `profile_gate_status` | `green` |
| `dev_control_enabled` | `false` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `rescue_agent_router_status` | `disabled_by_profile` |

JSON: `backend_down_after_release_restart_version_recovered.json`

## `/api/dev-dashboard/recent-evidence` (release)

HTTP **404**, Body:

```json
{"status":"error","code":"PROFILE_ROUTE_BLOCKED","path":"/api/dev-dashboard/recent-evidence"}
```

Evidence: `backend_down_after_release_restart_recent_evidence_release_block.txt`

## Pflichtbewertung

| Feld | Wert |
|------|------|
| **Status** | **ok** |
