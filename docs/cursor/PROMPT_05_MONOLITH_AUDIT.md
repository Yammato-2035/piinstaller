# Prompt 05 – Monolith-Audit (nur Analyse)

STRICT MODE – MONOLITH AUDIT ONLY

ZIEL:
Modulgrenzen dokumentieren, **kein** Refactoring.

NICHT ERLAUBT:
- keine Refactorings, keine Dateiverschiebungen, keine API-Änderungen, keine neuen Features

PHASE 1 – SCAN: Backend, Routen, Backup/Verify/Restore/Inspect/Safety/Rescue

PHASE 2 – DOMÄNEN: core.backup, core.verify, … (siehe DOMAIN_BOUNDARIES.md)

PHASE 3 – KOPPLUNGEN: gefährliche Abhängigkeiten, Legacy-Namen, fehlende Tests

PHASE 4 – OUTPUT:
- `docs/architecture/DOMAIN_BOUNDARIES.md` (vollständig)
- `docs/roadmap/MONOLITH_REFACTOR_PLAN.md`
- `docs/evidence/release-gates/backend_dependency_graph.json`
- `docs/evidence/release-gates/dangerous_couplings.json`
- `docs/evidence/release-gates/api_domain_mapping.json`

ABSCHLUSSBERICHT: Domänen, Kopplungen, Refactoring-Reihenfolge, fehlende Tests.
