# DCC Delegation Cleanup — Phase F.4 (EN)

**HEAD:** post F.4 · **Status:** done

## Goal

Route remaining safe HTTP DCC couplings through `dcc_status_facade` — no API/response changes.

## Migrated

| Target | Facade function |
|--------|-----------------|
| `POST /api/ai/prompt/generate` | `build_dcc_cursor_meta_prompt_api` |
| `GET .../backend-health` | `build_dcc_backend_health_api` |
| `GET .../notifications/status` | `build_dcc_notifications_status_api` |
| `GET .../notifications/events` | `build_dcc_notifications_events_api` |
| `GET .../evidence-index` | `build_dcc_evidence_index_api` |

## Guarantees

- No new aggregation/traffic-light/notification logic
- Profile gate unchanged
- Responses unchanged (legacy shape via unwrap)

## Remaining (allowed)

- `deploy_job_state` → `build_dashboard_status` (core-internal, F.5)
- Roadmap subrouter → `load_roadmap_registry_bundle` (registry-only)

## Next step

**G.1** System Status Facade · **G.2** Network Info Facade
