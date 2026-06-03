# Ports and Profiles — Live Check

**Datum:** 2026-06-03

## `/api/version` (Runtime `/opt`)

| Feld | Wert |
|------|------|
| HTTP 200 | **yes** |
| `runtime_ports` in Response | **no** (Workspace-Code noch nicht nach `/opt` deployt) |
| `install_profile` | **release** |
| `dev_control_enabled` | **false** |

Nach Operator-`deploy-to-opt.sh`: erwartet `runtime_ports.backend_api.port=8000`, `canonical_urls.dcc`, `port_registry_source`.

## Workspace TestClient (Code in diesem Commit)

**5 passed** `test_runtime_ports_v1.py` — `/api/version` enthält Ports im Workspace.

## `/api/dev-dashboard/backend-health` unter release

| Feld | Wert |
|------|------|
| HTTP | **404** |
| Code | **PROFILE_ROUTE_BLOCKED** |

Evidence: `ports_and_profiles_backend_health_release_expected_block.txt`

| **Status** | **ok** (Gating); Registry-Live in `/api/version` nach Deploy |
