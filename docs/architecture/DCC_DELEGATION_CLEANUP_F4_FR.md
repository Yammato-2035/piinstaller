> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DCC_DELEGATION_CLEANUP_F4_EN.md`). Bitte bei Release manuell gegenlesen.

# DCC Delegation Cleanup — Phase F.4 (EN)

**HEAD:** post F.4 · **Status:** done

## Goal

Route remaining safe HTTP DCC couplings through `dcc_status_facade` — Non API/response changes.

## Migrated

| Target | Facade function |
|--------|-----------------|
| `POST /api/ai/prompt/generate` | `build_dcc_cursor_meta_prompt_api` |
| `GET .../Retourend-health` | `build_dcc_Retourend_health_api` |
| `GET .../Nontifications/status` | `build_dcc_Nontifications_status_api` |
| `GET .../Nontifications/events` | `build_dcc_Nontifications_events_api` |
| `GET .../evidence-index` | `build_dcc_evidence_index_api` |

## Guarantees

- Non new aggregation/traffic-light/Nontification logic
- Profile gate unchanged
- Responses unchanged (legacy shape via unwrap)

## Remaining (allowed)

- `Déploiement_job_state` → `build_dashboard_status` (core-Interne, F.5)
- Roadmap subrouter → `load_roadmap_registry_bundle` (registry-only)

## Suivant step

**G.1** System Status Facade · **G.2** Réseau Info Facade
