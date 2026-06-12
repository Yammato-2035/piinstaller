# APP Safe Next Slices — Phase E.7 (E.8-Vorschlag)

**HEAD:** `72a7c93` · **Audit-only** — keine Extraktion in E.7

## Zulässige E.8-Kandidaten

Nur GET, read-only, kein subprocess/systemctl, keine DCC-Vollaggregation, vorhandenes Core-Modul.

| Route | Methode | Domain | Risiko | vorgeschlagener Router | Grund |
|-------|---------|--------|--------|------------------------|-------|
| `/api/dev-dashboard/backend-health` | GET | dev_dashboard | low | `dev_dashboard_readonly.py` (Erweiterung) | `load_backend_health_snapshot`; DCC-Profil-Gate via `build_dcc_profile_block_response`; Evidence-JSON only |
| `/api/dev-dashboard/notifications/status` | GET | dev_dashboard | low | `dev_dashboard_readonly.py` (Erweiterung) | `core.notification_state.build_notification_summary`; rein lesend |
| `/api/dev-dashboard/notifications/events` | GET | dev_dashboard | low | `dev_dashboard_readonly.py` (Erweiterung) | `core.notification_state.list_notification_events`; Query-Limit only |

## Empfohlener E.8-Slice

**3 Routen** in einem Slice — Erweiterung von `api/routes/dev_dashboard_readonly.py`:

- Kein neues Router-Modul nötig (Module-Reuse)
- Kein `build_dashboard_status`
- Tests analog `test_app_router_slice_e4.py`

## Bewusst nicht E.8

| Route | Grund |
|-------|-------|
| `GET /api/radio/*` | Proxy/Cache-Helfer und App-Globals in `app.py`; kein `core.radio`-Modul |
| `GET /api/update-center/*` | Edition-Gate (`get_app_edition() == "repo"`) inline; Logik noch in `app.py` |
| `GET /api/radio/dsi-config/*` | Datei-IO-Helfer `_dsi_*` nur in Monolith |
| `GET /api/system/freenove-detection` | `run_command` / i2c in Handler-Helfer |

## Nächster Schritt nach E.8

Facade-Phase für blockierte Aggregations-Routen (siehe `APP_BLOCKED_ROUTES_E7.md`, `APP_NEXT_FACADE_CANDIDATES_E7.md`).
