# Fleet Heartbeat — Smoke nach Script-Fix

**Stand:** 2026-06-02  
**Status:** **ok**  
**Smoke-Artefakte:** `fleet_heartbeat_fix_after_script_fix_20260602_164249/`

## Session

| Feld | Wert |
|------|------|
| `RUN_ID` | `manual_fleet_heartbeat_fix_after_script_fix_20260602_164249` |
| `SESSION_ID` | `fleet-manual_fleet_heartbeat_fix_after_script_fix_20260602_164249` |
| Skript | `/opt/setuphelfer/scripts/rescue-live/fleet-session-api.sh` (Fix live) |

## Ergebnis

| Schritt | Exit | JSON | Code / Zustand |
|---------|------|------|----------------|
| Create | 0 | OK | Session angelegt |
| Heartbeat `running` | 0 | OK | `FLEET_SESSION_HEARTBEAT_OK`, `agent_state=alive`, `status=starting` |
| Finish `success` | 0 | OK | `FLEET_SESSION_FINISHED` |
| Final list | — | — | `final_status=success`, `final_agent_state=alive`, `finished_at` gesetzt |

## Regression `status=running`

**Behoben live:** kein `FLEET_SESSION_BLOCKED_INVALID_PAYLOAD`; `agent_state=alive`.

## Root-Cause-Closure

`fleet_script_bash_parameter_expansion_corrupts_json_payload` → **resolved** in `55b7bce`, live nach `/opt`-Script-Sync.

## Einordnung (final)

| Thema | Status |
|-------|--------|
| Fleet Heartbeat Fix | **green / ok** |
| Root Cause | **resolved_in_55b7bce** |
| Weitere Fleet-Session | **nicht nötig** |
| Release-Restore | **ok** (`release_restore_blocked_sudo_required=resolved`) |
| DCC-Port-Mapping | **green** |
| Weitere Fleet-Session | **nicht nötig** |

## Guards

Kein ISO, QEMU, USB, Backup, Restore, Fake-VM.
