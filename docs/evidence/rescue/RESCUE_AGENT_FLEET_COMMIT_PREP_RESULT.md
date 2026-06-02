# Rescue Agent / Fleet — Commit-Prep Ergebnis

**Stand:** 2026-06-02  
**Basis-HEAD:** `00615d5`

## Tests (Workspace)

| Prüfung | Ergebnis |
|---------|----------|
| Runtime-Import (9 Module) | OK |
| py_compile (fleet + rescue_agent + install_profile) | OK |
| pytest Rescue/Fleet (7 Dateien) | **32 passed** |
| pytest `test_app_router_registry_v1` + `test_fleet_session_state_v1` | **13 passed** |
| Frontend build | OK |
| Frontend Vitest | **54 passed** |

## Contract-Status

| Bereich | Status |
|---------|--------|
| E2EE | `contract_stub_only` |
| nftables | `preview_only_apply_false` |
| Rescue Agent | Stub/Contract, nicht produktiver Live-Agent |
| Fleet Heartbeat | `agent_state` getrennt; `running` neutralisiert |

## Commit

- Selektives Staging (kein `git add -A`)
- Message: `Add rescue agent fleet heartbeat contract stubs`
- Push: **nein**

## Deploy

- Deploy-Drift **unverändert offen** bis Operator-Sync
- Siehe `docs/evidence/dev-dashboard/POST_RESCUE_AGENT_COMMIT_DEPLOY_SYNC_REQUIRED.md`
