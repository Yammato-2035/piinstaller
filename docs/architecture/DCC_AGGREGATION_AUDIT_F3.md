# DCC Aggregation Audit — Phase F.3

**HEAD:** `8bb910c` · **Typ:** reine Analyse (kein Refactoring)

## Ergebnis

| Bereich | Bewertung |
|---------|-----------|
| Kanonische Facade | `dcc_status_facade` — 6 Routen migriert (F.2) |
| Verbleibende Direktzugriffe | 1× `app.py` (ai_prompt), 1× `deploy_job_state`, E.8 readonly |
| Roadmap Subrouter | `boundary_ok_registry_only` |
| ai_prompt_generate_stub | `migrate_to_dcc_status_facade` (F.4) |
| Deploy/Core-Coupling | akzeptabel intern; Gate → Facade-Hook empfohlen |
| Status-Duplikate | Cockpit, Overview, Frontend — ViewModel/Facade Konsolidierung F.4+ |

## Evidence

| Dokument | Inhalt |
|----------|--------|
| [DCC_DIRECT_USAGE_AUDIT_F3.md](../evidence/app-monolith/DCC_DIRECT_USAGE_AUDIT_F3.md) | Direktzugriffe |
| [DCC_STATUS_DUPLICATE_ANALYSIS_F3.md](../evidence/app-monolith/DCC_STATUS_DUPLICATE_ANALYSIS_F3.md) | Ampel-Duplikate |
| [ROADMAP_SUBROUTER_BOUNDARY_F3.md](../evidence/app-monolith/ROADMAP_SUBROUTER_BOUNDARY_F3.md) | Subrouter |
| [AI_PROMPT_GENERATE_STUB_F3.md](../evidence/app-monolith/AI_PROMPT_GENERATE_STUB_F3.md) | AI Stub |
| [DCC_DEPLOY_CORE_COUPLING_F3.md](../evidence/app-monolith/DCC_DEPLOY_CORE_COUPLING_F3.md) | Deploy-Kopplung |
| [BOUNDARY_WARNINGS_F3.txt](../evidence/app-monolith/BOUNDARY_WARNINGS_F3.txt) | Guards |

## Guards (F.3)

Neue WARN-only Checks in `scripts/check-module-boundaries.sh`:

- `dcc_direct_build_dashboard_status_outside_facade`
- `dcc_direct_roadmap_bundle_in_router`
- `dcc_duplicate_ampel_status_mapping`
- `dcc_prompt_generate_uses_dashboard_status`
- `dcc_deploy_core_cross_coupling`
- `dcc_frontend_status_viewmodel_missing`

## Nächster Schritt

**F.4** — `ai_prompt_generate_stub` + readonly-Router auf Facade-Sections. Siehe [DCC_NEXT_MIGRATIONS_F3.md](DCC_NEXT_MIGRATIONS_F3.md).

## i18n

Keine UI-Änderung — siehe [I18N_DOC_COMPLETENESS_F3.md](../evidence/app-monolith/I18N_DOC_COMPLETENESS_F3.md).
