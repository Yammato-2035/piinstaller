# ISO-Precheck-Readiness nach Deploy 2e602d0

**Stand:** 2026-06-02  
**ISO-Build:** nein

## Bewertung

| Kriterium | Status |
|-----------|--------|
| App-Bootstrap (committed) | ok |
| Router Registry / Startup Diagnostics | ok (Code) |
| Core Facades | ok |
| Rescue-Agent/Fleet (committed) | stub_ok |
| Deploy nach `/opt` | **blocked** (`sudo`) |
| Deploy-Drift | **red** |
| Runtime-Gate live | **yellow** (release + legacy dashboard) |
| DCC-Smoke | **blocked** |
| Fleet Heartbeat live | **blocked** |

## ISO-Precheck-Gesamtstatus

**`blocked_by_deploy_drift`**

Erst nach erfolgreichem `deploy-to-opt.sh` + Restart + grünem Drift-Gate + optional Fleet-Live-Smoke:

→ `ready_for_controlled_iso_build_precheck`

**Nicht** bedeutet: ISO gebaut, USB bereit, Rettungsstick fertig.
