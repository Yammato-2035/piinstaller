# Fleet Finish Exit-1 — Triage-Ergebnis

**Stand:** 2026-06-02  
**Triage-Artefakte:** `docs/evidence/dev-dashboard/fleet_finish_exit1_triage_20260602_162848/`  
**Session (Operator):** `fleet-manual_fleet_heartbeat_fix_20260602_162012`

## Kurzfassung

**Root Cause:** `fleet_script_bash_parameter_expansion_corrupts_json_payload`  
In `fleet_session_patch()` zerstörte `payload="${3:-{}}"` jedes JSON mit `}` im Wert (bash-Parser beendet die Expansion zu früh). `fleet_validate_json` scheiterte → **Exit 1**, **leerer stdout** — kein API-Aufruf.

Die API (`POST .../finish`) liefert bei gültigem JSON **HTTP 200** / `FLEET_SESSION_FINISHED`.

**Fix (Workspace):** `payload="${3-}"` + leerer Default `{}` — verifiziert (`finish_ec=0`).

## Runtime zum Triage-Zeitpunkt

| Prüfung | Ergebnis |
|---------|----------|
| `install_profile` | **local_lab** |
| `/api/fleet/sessions` | **HTTP 200** |
| Profil-Gate | Exit **0** |
| Legacy Deploy-Gate | Exit **0** |
| Session gefunden | **ja** |
| `status` vor Finish-Versuch | `timeout_warning` (stale rules; kein `starting`) |
| `agent_state` | `booting` |
| `finished_at` | `null` |

Kein `release_profile_blocks_fleet` zum Messzeitpunkt.

## Beweiskette

| Schritt | Exit | Ergebnis |
|---------|------|----------|
| `fleet_session_finish_payload success` | 0 | valides JSON (316 B) |
| `fleet_validate_json` auf **direktem** `$P` | 0 | OK |
| `fleet_validate_json` via `${3:-{}}` in Funktion | **1** | JSON korrupt (+extra `}`) |
| `fleet_session_patch finish` (vor Fix) | **1** | leerer Body, kein curl |
| `curl` direkt mit gleichem Payload | **200** | `FLEET_SESSION_FINISHED` |
| `fleet_session_patch finish` (nach Fix) | **0** | valides JSON |

## Sekundärfaktoren

1. **`source fleet-session-api.sh`** aktiviert `set -euo pipefail` in der Caller-Shell → Exit 1 bricht sofort ab.
2. Pipe `fleet_session_patch … \| python3 -m json.tool` bei leerem stdout → zusätzlich `json.tool`-Fehler (Folge, nicht Ursache).
3. **`set -e` nach source** verstärkt das Verhalten.

## Nach Fix (neue Session)

`fleet-triage_finish_fix_verify_163549`: Heartbeat `running` → `agent_state=alive`, Finish **OK**.

## Operator-Session `…162012`

Während Triage per direktem `curl` auf **success** / `finished_at` gesetzt (Re-Finish HTTP 200). Für erneuten End-to-End-Smoke neue Session anlegen.

## Nächste Aktion

1. Script-Fix nach `/opt` deployen (Operator, separater Lauf).
2. Release-Profil-Handoff siehe `FLEET_FINISH_EXIT1_RELEASE_PROFILE_HANDOFF.md` (`local_lab` noch aktiv).
3. Fleet-Smoke mit **neuer** Session + gefixtem Skript wiederholen.
