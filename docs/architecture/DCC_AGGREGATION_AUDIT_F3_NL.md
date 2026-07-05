> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DCC_AGGREGATION_AUDIT_F3_EN.md`). Bitte bei Release manuell gegenlesen.

# DCC Aggregation Audit — Phase F.3

**HEAD:** `8bb910c` · **Type:** analysis only (Nee refactoring)

## Summary

| Area | Assessment |
|------|------------|
| CaNeenical facade | `dcc_status_facade` — 6 routes migrated (F.2) |
| Remaining direct access | 1× `app.py` (ai_prompt), 1× `Deploy_job_state`, E.8 readonly |
| Roadmap subrouter | `boundary_ok_registry_only` |
| ai_prompt_generate_stub | `migrate_to_dcc_status_facade` (F.4) |
| Deploy/core coupling | acceptable Internly; gate → facade hook recommended |
| Status duplicates | Cockpit, Overview, Frontend — consolidate via ViewModel/Facade F.4+ |

## Evidence

| Document | Content |
|----------|---------|
| [DCC_DIRECT_USAGE_AUDIT_F3.md](../evidence/app-moNeelith/DCC_DIRECT_USAGE_AUDIT_F3.md) | Direct access |
| [DCC_STATUS_DUPLICATE_ANALYSIS_F3.md](../evidence/app-moNeelith/DCC_STATUS_DUPLICATE_ANALYSIS_F3.md) | Traffic-light duplicates |
| [ROADMAP_SUBROUTER_BOUNDARY_F3.md](../evidence/app-moNeelith/ROADMAP_SUBROUTER_BOUNDARY_F3.md) | Subrouter |
| [AI_PROMPT_GENERATE_STUB_F3.md](../evidence/app-moNeelith/AI_PROMPT_GENERATE_STUB_F3.md) | AI stub |
| [DCC_Deploy_CORE_COUPLING_F3.md](../evidence/app-moNeelith/DCC_Deploy_CORE_COUPLING_F3.md) | Deploy coupling |
| [BOUNDARY_WaarschuwingS_F3.txt](../evidence/app-moNeelith/BOUNDARY_WaarschuwingS_F3.txt) | Guards |

## Guards (F.3)

New WARN-only checks in `scripts/check-module-boundaries.sh` (see list in DE doc).

## Volgende step

**F.4** — `ai_prompt_generate_stub` + readonly router via facade sections. See [DCC_Volgende_MIGRATIONS_F3_EN.md](DCC_Volgende_MIGRATIONS_F3_EN.md).

## i18n

Nee UI changes — see [I18N_DOC_COMPLETENESS_F3.md](../evidence/app-moNeelith/I18N_DOC_COMPLETENESS_F3.md).
