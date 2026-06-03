# Developer Backend Watchdog — Timer Handoff Ready

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| Timer service example | **yes** — `packaging/systemd/setuphelfer-dev-healthcheck.service.example` |
| Timer example | **yes** — `packaging/systemd/setuphelfer-dev-healthcheck.timer.example` |
| Timer automatisch aktiviert | **no** |
| Runbook vorhanden | **yes** — `docs/runbooks/DEVELOPER_BACKEND_WATCHDOG_RUNBOOK.md` |
| **Status** | **ready_optional** |

Intervall (Beispiel): `OnUnitActiveSec=60s`. Aktivierung nur nach Deploy und separater Operator-Freigabe.
