# DCC Delegation Cleanup — Phase F.4

**HEAD:** nach F.4 · **Status:** erledigt

## Ziel

Letzte sichere HTTP-DCC-Kopplungen auf `dcc_status_facade` zurückführen — ohne API-/Response-Änderung.

## Migriert

| Ziel | Facade-Funktion |
|------|-----------------|
| `POST /api/ai/prompt/generate` | `build_dcc_cursor_meta_prompt_api` |
| `GET .../backend-health` | `build_dcc_backend_health_api` |
| `GET .../notifications/status` | `build_dcc_notifications_status_api` |
| `GET .../notifications/events` | `build_dcc_notifications_events_api` |
| `GET .../evidence-index` | `build_dcc_evidence_index_api` |

## Garantien

- Keine neue Aggregations-/Ampel-/Notification-Logik
- Profil-Gate unverändert
- Responses byte-identisch (Legacy-Shape via Unwrap)

## Verbleibend (erlaubt)

- `deploy_job_state` → `build_dashboard_status` (Core-intern, F.5)
- Roadmap-Subrouter → `load_roadmap_registry_bundle` (registry-only)

## Nächster Schritt

**G.1** System Status Facade · **G.2** Network Info Facade

Evidence: `docs/evidence/app-monolith/DCC_READONLY_DELEGATION_F4.md`
