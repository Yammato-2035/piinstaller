> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DCC_DELEGATION_CLEANUP_F4_EN.md`). Bitte bei Release manuell gegenlesen.

# DCC Delegation Cleanup — Phase F.4 (EN)

**HEAD:** post F.4 · **Status:** done

## Goal

Route remaining safe HTTP DCC couplings through `dcc_status_facade` — Nee API/response changes.

## Migrated

| Target | Facade function |
|--------|-----------------|
| `POST /api/ai/prompt/generate` | `build_dcc_cursor_meta_prompt_api` |
| `GET .../Terugend-health` | `build_dcc_Terugend_health_api` |
| `GET .../Neetifications/status` | `build_dcc_Neetifications_status_api` |
| `GET .../Neetifications/events` | `build_dcc_Neetifications_events_api` |
| `GET .../evidence-index` | `build_dcc_evidence_index_api` |

## Guarantees

- Nee new aggregation/traffic-light/Neetification logic
- Profile gate unchanged
- Responses unchanged (legacy shape via unwrap)

## Remaining (allowed)

- `Deploy_job_state` → `build_dashboard_status` (core-Intern, F.5)
- Roadmap subrouter → `load_roadmap_registry_bundle` (registry-only)

## Volgende step

**G.1** System Status Facade · **G.2** Netwerk Info Facade
