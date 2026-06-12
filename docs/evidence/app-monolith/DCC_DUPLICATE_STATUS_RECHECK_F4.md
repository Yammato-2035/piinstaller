# DCC Duplicate Status Recheck — Phase F.4

**HEAD:** nach F.4

## Prüfung

| Domäne | Parallelstruktur neu? | Bewertung |
|--------|----------------------|-----------|
| Statusmapping HTTP | nein | Facade-API-Helper entpacken nur Sections |
| Notification Summary | nein | `build_dcc_notifications_status_api` → Section → Core |
| Backend Health | nein | `build_dcc_backend_health_api` → Section → Core |
| Evidence Index | nein | `build_dcc_evidence_index_api` → Section → Core |
| Ampel in Routern | nein | keine Router-Normalisierung hinzugefügt |

## Ergebnis

**Keine neue Parallelstruktur.** F.4 fügt nur dünne API-Wrapper hinzu, die bestehende Section-Builder nutzen.

Verbleibende Duplikate (F.3, unverändert):
- Cockpit `_normalize_ampel`
- Project Overview `_normalize_status`
- Frontend `trafficLightModel.ts`
- `deploy_job_state` Runtime-Gate

Nächster Track: G.1 System Status Facade, Frontend ViewModel.
