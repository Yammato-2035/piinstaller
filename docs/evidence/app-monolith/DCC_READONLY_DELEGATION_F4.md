# DCC Readonly Delegation — Phase F.4

**Modul:** `backend/api/routes/dev_dashboard_readonly.py`

## Migrierte Endpoints

| Route | Vorher | Nachher |
|-------|--------|---------|
| `GET .../backend-health` | `load_backend_health_snapshot` | `build_dcc_backend_health_api` |
| `GET .../notifications/status` | `build_notification_summary` + code | `build_dcc_notifications_status_api` |
| `GET .../notifications/events` | `list_notification_events` + code | `build_dcc_notifications_events_api` |
| `GET .../evidence-index` | `build_evidence_index` | `build_dcc_evidence_index_api` |

## Unverändert

- Profil-Gate auf `backend-health` (`build_dcc_profile_block_response`)
- Response-Shapes (Legacy-API-Wrapper entpacken Section-Daten)
- `modules`, `manual-command-runs`, `recent-evidence` (kein Facade-Aggregat nötig)

## Neue Facade-API-Helper

In `dcc_status_facade.py` — reine Delegation/Unwrap, keine neue Logik.
