# Deploy-Sync 2e602d0 — Post-Deploy Ergebnis

**Stand:** 2026-06-02  
**Status:** **blocked** (`deploy_blocked_sudo_required`)

## Deploy / Restart

| Aktion | Ergebnis |
|--------|----------|
| `deploy-to-opt.sh` | **nicht ausgeführt** |
| `systemctl restart setuphelfer-backend.service` | **nicht ausgeführt** |

## Runtime nach geplantem Deploy (nicht gemessen — Baseline unverändert)

| Prüfung | Erwartung nach erfolgreichem Deploy | Aktuell (readonly) |
|---------|--------------------------------------|---------------------|
| `rescue_agent/` unter `/opt` | vorhanden | **fehlt** |
| `app_bootstrap/` unter `/opt` | vorhanden | **fehlt** |
| `/api/version` Diagnosefelder | gesetzt | **fehlt** |
| `deploy_drift` | green | **offen** |
| Legacy Runtime-Gate | profilabhängig | unverändert |

## Operator-Aktion erforderlich

Siehe `DEPLOY_SYNC_2E602D0_SOURCE_VERIFICATION.md`.

Nach Deploy erneut ausführen:

```bash
./scripts/check-runtime-deploy-gate.sh
./scripts/check-runtime-profile-deploy-gate.sh
curl -sS http://127.0.0.1:8000/api/version | jq .
```
