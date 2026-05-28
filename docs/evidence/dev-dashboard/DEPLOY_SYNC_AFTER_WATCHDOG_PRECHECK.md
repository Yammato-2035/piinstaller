# Deploy-Sync nach Watchdog — Precheck

**Datum:** 2026-05-28  
**Operator-Freigabe:** `DEPLOY_HELPER_SYNC_FREIGEGEBEN`  
**HEAD:** `2bf64b7` auf `main`

## Gate vor Deploy

```text
./scripts/check-runtime-deploy-gate.sh → Exit 14 (deploy_drift)
```

## Ziel

Workspace-Stand (liveness, Gate 17/18, Dashboard-Timeouts, Frontend-Fail-State) nach `/opt/setuphelfer` via `setuphelfer-deploy-helper.service`.

JSON: `deploy_sync_after_watchdog_precheck_latest.json`
