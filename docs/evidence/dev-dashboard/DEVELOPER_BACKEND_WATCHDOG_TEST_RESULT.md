# Developer Backend Watchdog — Test Result

**Datum:** 2026-06-03

| Lauf | Ergebnis |
|------|----------|
| `bash -n check-backend-health.sh` | **ok** |
| `bash -n deploy-to-opt.sh` | **ok** |
| `pytest test_dev_dashboard_backend_health_v1.py` | **6 passed** |
| `pytest test_dev_dashboard_recent_evidence_v1.py` | **5 passed** |
| Broad `-k backend_health or dev_dashboard` | nicht vollständig (collection noise) |
| `npm run build` | **ok** |
| `npm run test -- --run` | **54 passed** |

| Feld | Wert |
|------|------|
| **Status** | **partial** (broad pytest skipped; Kern grün) |
