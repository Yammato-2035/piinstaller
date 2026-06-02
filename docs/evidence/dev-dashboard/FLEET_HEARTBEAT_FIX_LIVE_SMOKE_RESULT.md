# Fleet Heartbeat Fix — Live-Smoke

**Stand:** 2026-06-02  
**Status:** **review_required** (Exit-1 triagiert: Script-Bug `${3:-{}}`; API Finish OK per curl; Fix im Workspace)

**Triage:** `FLEET_FINISH_EXIT1_TRIAGE_RESULT.md`, `fleet_finish_exit1_triage_20260602_162848/`

## Geplanter Ablauf (nach Deploy + local_lab)

1. `RUN_ID=manual_fleet_heartbeat_fix_<UTC>`
2. `POST /api/fleet/sessions` (create)
3. `POST .../heartbeat` mit Legacy-Payload `status=running`
4. Erwartung: kein `FLEET_SESSION_BLOCKED_INVALID_PAYLOAD`; `agent_state=alive`
5. `POST .../finish`
6. Evidence unter `docs/evidence/runtime-results/dev-dashboard/`

## Skript

`scripts/rescue-live/fleet-session-api.sh` — Heartbeat neutralisiert `running` → `agent_state=alive`.

## Dieser Lauf

| Prüfung | Ergebnis |
|---------|----------|
| Live Create/Heartbeat/Finish | **not_run** |
| `status=running` live behoben | **not_verified** |

## Voraussetzungen

1. Operator-Deploy aus Worktree `2e602d0`
2. `local_lab` Drop-in + Restart
3. `./scripts/check-runtime-profile-deploy-gate.sh` Exit 0
