# Developer Backend Watchdog — systemd Timer Design

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| Timer vorbereitet | **yes** |
| Dateien | `packaging/systemd/setuphelfer-dev-healthcheck.service.example`, `.timer.example` |
| Automatisch aktiv | **no** |
| Read-only | **yes** |
| Kein Restart | **yes** |
| Intervall (Beispiel) | 60s (`OnUnitActiveSec=60s`) |
| Exec | `scripts/dev-dashboard/check-backend-health.sh` |
| **Status** | **ok** |
