# DCC Aggregation Audit — Phase F.3

**HEAD:** `8bb910c` · **Type:** analysis only (no refactoring)

## Summary

| Area | Assessment |
|------|------------|
| Canonical facade | `dcc_status_facade` — 6 routes migrated (F.2) |
| Remaining direct access | 1× `app.py` (ai_prompt), 1× `deploy_job_state`, E.8 readonly |
| Roadmap subrouter | `boundary_ok_registry_only` |
| ai_prompt_generate_stub | `migrate_to_dcc_status_facade` (F.4) |
| Deploy/core coupling | acceptable internally; gate → facade hook recommended |
| Status duplicates | Cockpit, Overview, Frontend — consolidate via ViewModel/Facade F.4+ |

## Evidence

| Document | Content |
|----------|---------|
| [DCC_DIRECT_USAGE_AUDIT_F3.md](../evidence/app-monolith/DCC_DIRECT_USAGE_AUDIT_F3.md) | Direct access |
| [DCC_STATUS_DUPLICATE_ANALYSIS_F3.md](../evidence/app-monolith/DCC_STATUS_DUPLICATE_ANALYSIS_F3.md) | Traffic-light duplicates |
| [ROADMAP_SUBROUTER_BOUNDARY_F3.md](../evidence/app-monolith/ROADMAP_SUBROUTER_BOUNDARY_F3.md) | Subrouter |
| [AI_PROMPT_GENERATE_STUB_F3.md](../evidence/app-monolith/AI_PROMPT_GENERATE_STUB_F3.md) | AI stub |
| [DCC_DEPLOY_CORE_COUPLING_F3.md](../evidence/app-monolith/DCC_DEPLOY_CORE_COUPLING_F3.md) | Deploy coupling |
| [BOUNDARY_WARNINGS_F3.txt](../evidence/app-monolith/BOUNDARY_WARNINGS_F3.txt) | Guards |

## Guards (F.3)

New WARN-only checks in `scripts/check-module-boundaries.sh` (see list in DE doc).

## Next step

**F.4** — `ai_prompt_generate_stub` + readonly router via facade sections. See [DCC_NEXT_MIGRATIONS_F3_EN.md](DCC_NEXT_MIGRATIONS_F3_EN.md).

## i18n

No UI changes — see [I18N_DOC_COMPLETENESS_F3.md](../evidence/app-monolith/I18N_DOC_COMPLETENESS_F3.md).
