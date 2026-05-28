# Deploy-Sync nach Watchdog — Precheck

**Datum:** 2026-05-28 (Wiederholung)  
**Operator-Freigabe:** `DEPLOY_HELPER_SYNC_FREIGEGEBEN`  
**HEAD:** `5b4a874` (Watchdog-Code in `2bf64b7`)

## Gate vor Deploy

```text
./scripts/check-runtime-deploy-gate.sh → Exit 14 (deploy_drift)
```

## Deploy-Helper

Zweiter Agent-Versuch: `sudo -n systemctl start setuphelfer-deploy-helper.service` → Passwort erforderlich, Service inactive.

JSON: `deploy_sync_after_watchdog_precheck_latest.json`
