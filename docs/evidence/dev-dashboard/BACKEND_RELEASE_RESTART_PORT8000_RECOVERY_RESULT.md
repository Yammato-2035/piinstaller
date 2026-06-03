# Backend Release Restart — Port 8000 Recovery

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| Agent sudo recovery | **nicht ausgeführt** |
| Backend jetzt (Phase 0) | **active**, Port **8000** listening |
| `/api/version` HTTP 200 | **yes** |
| `install_profile` | **release** |
| **Status** | **recovered** (Operator/systemd; nicht in diesem Agent-Lauf neu gestartet) |

Operator-Handoff bei erneutem Ausfall:

```bash
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
# 15×2s auf /api/version warten (deploy-to-opt.sh)
```
