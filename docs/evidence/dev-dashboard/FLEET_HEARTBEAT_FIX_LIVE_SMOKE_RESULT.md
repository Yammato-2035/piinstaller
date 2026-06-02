# Fleet Heartbeat Fix — Live-Smoke (Gesamtstatus)

**Stand:** 2026-06-02  
**Status:** **grün** (neue Session nach Script-Fix; API immer Port **8000**)

## Port-Hinweis

- Fleet- und Dev-Dashboard-API-Smokes: **`http://127.0.0.1:8000`**
- Browser-Port **8080** (nginx) ist **irrelevant** für Fleet — siehe `DCC_PORT_MAPPING_RESULT.md`

## Root Cause (Exit-1)

`fleet_script_bash_parameter_expansion_corrupts_json_payload` — `${3:-{}}` in `fleet_session_patch` korrumpierte JSON.

**Fix:** Commit `55b7bce` → `payload="${3-}"`  
**In `/opt`:** **yes** (grep `${3-}` in `/opt/setuphelfer/scripts/rescue-live/fleet-session-api.sh`)

## Sauberer Live-Smoke (belegt)

| Feld | Wert |
|------|------|
| Evidence | `FLEET_HEARTBEAT_FIX_AFTER_SCRIPT_FIX_RESULT.md` |
| Session | `fleet-manual_fleet_heartbeat_fix_after_script_fix_20260602_164249` |
| Create → Heartbeat(`running`) → Finish | **ok** |

## Nicht verwenden

| Session | Grund |
|---------|--------|
| `fleet-manual_fleet_heartbeat_fix_20260602_162012` | Während Exit-1-Triage per direktem `curl` beendet/manipuliert |

## Vor Exit-1-Triage

Geplanter API-Smoke war korrekt gegen **:8000**; Shell-Exit 1 kam vom Wrapper, nicht von der API.

## Release

**Wiederhergestellt:** `release_restore_status=ok`; `local_lab_open_after_smoke=false`.

| API unter `release` | Bewertung |
|---------------------|-----------|
| `/api/dev-dashboard/status` | **expected_profile_block** |
| `/api/fleet/sessions` | **expected_profile_block** |

Keine weitere Fleet-Session erforderlich.
