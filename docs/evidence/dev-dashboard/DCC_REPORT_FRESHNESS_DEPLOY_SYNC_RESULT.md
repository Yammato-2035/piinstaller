# DCC Report Freshness — Deploy Sync Result

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| Deploy ausgeführt | **no** (Agent-Kontext) |
| Deploy Exit | **1** |
| Fehler | `sudo: Ein Passwort ist notwendig` |
| Log | `docs/evidence/dev-dashboard/dcc_deploy_sync_terminal_latest.log` |

## Operator-Aktion erforderlich

```bash
cd /home/volker/piinstaller
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
# oder:
sudo systemctl start setuphelfer-deploy-helper.service
```

Nach erfolgreichem Deploy: local_lab-Smoke gemäß Runbook wiederholen.

**Status:** `blocked` (`deploy_failed`)
