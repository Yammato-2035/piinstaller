# APP Router Slice — Phase E.8

**Baseline HEAD:** `cdc391e` (nach E.7 Audit)

## E.8-Slice Bestätigung

| Route | Core-Modul | Core-Funktion | Methode | Risiko | E.8 geeignet |
|-------|------------|---------------|---------|--------|--------------|
| `/api/dev-dashboard/backend-health` | `core.dev_dashboard_backend_health` | `load_backend_health_snapshot` | GET | low | **ja** |
| `/api/dev-dashboard/notifications/status` | `core.notification_state` | `build_notification_summary` | GET | low | **ja** |
| `/api/dev-dashboard/notifications/events` | `core.notification_state` | `list_notification_events` | GET | low | **ja** |

Profil-Gate für backend-health: `core.dev_dashboard_status_service.build_dcc_profile_block_response` (bestehend, keine neue Logik).

## Ausschlüsse

| Route | Grund |
|-------|-------|
| `GET /api/dev-dashboard/status` | DCC-Vollaggregation |
| `GET /api/status` | System Status Facade fehlt |
| `GET /api/system/network` | Network Info Facade fehlt |
| Backup/Restore/Deploy/Rescue/Partition-Write | CRITICAL — nicht extrahiert |

## Ziel-Router

`backend/api/routes/dev_dashboard_readonly.py` (Erweiterung E.4, jetzt 8 GET-Handler)

## Metriken (nach Extraktion)

| Metrik | vorher | nachher |
|--------|--------|---------|
| `app.py` Zeilen | 17.472 | 17.425 |
| `@app.*` Routen | 187 | 184 |
| `dev_dashboard_readonly.py` Zeilen | 62 | 112 |

## Nächster Schritt

**F.1** — DCC Status Facade (blockiert status/roadmap-root)
