# Release-Profil Restore — Phase 0 (vor Restore)

**Stand:** 2026-06-02  
**HEAD:** `6f2918a`  
**Branch:** `main`

## Services

| Service | Status |
|---------|--------|
| `setuphelfer-backend.service` | active |
| `setuphelfer.service` | active |

## Gates (vor Restore)

| Skript | Exit |
|--------|------|
| `check-runtime-profile-deploy-gate.sh` | 0 |
| `check-runtime-deploy-gate.sh` | 0 |

## Runtime (vor Restore)

| Feld | Wert |
|------|------|
| `install_profile` | `local_lab` |
| `profile_gate_status` | `green` |
| `dev_control_enabled` | `true` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |

## API (Port 8000)

| Endpoint | Status |
|----------|--------|
| `/api/dev-dashboard/status` | **200** (`status: success`) |
| `/api/fleet/sessions` | **200** (`FLEET_SESSION_LIST_OK`) |

## Fleet-Smoke

**Grün belegt:** Session `fleet-manual_fleet_heartbeat_fix_after_script_fix_20260602_164249` — Create → Heartbeat(`running`) → Finish OK. Evidence: `FLEET_HEARTBEAT_FIX_AFTER_SCRIPT_FIX_RESULT.md`. Root Cause `fleet_script_bash_parameter_expansion_corrupts_json_payload` → Fix `55b7bce` in `/opt`.

## DCC-Port-Mapping

**Grün:** UI/Cockpit `:3001`, API `:8000`, `:8080` = nginx (nicht SetupHelfer). Evidence: `DCC_PORT_MAPPING_RESULT.md`.

## Release-Restore erforderlich

**yes** — ISO-Precheck und produktive Gates erwarten `release`; `local_lab` war nur für Fleet-/DCC-Smoke.
