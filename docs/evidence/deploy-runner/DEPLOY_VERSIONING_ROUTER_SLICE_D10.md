# Deploy Versioning Router Slice (D.10)

**Ergebnis:** **8 Routen** extrahiert nach `routes_versioning.py`  
**facade_decoupling_d10:** true  
**allowed_to_execute:** false (alle Plan-Routen)

## Gewählter Slice (8)

| # | Route | Methode | runner_id |
|---|-------|---------|-----------|
| 1 | `/setuphelfer-runtime-identifier-migration` | POST | runner_setuphelfer_runtime_identifier_migration |
| 2 | `/setuphelfer-safe-rewrite-plan` | POST | runner_setuphelfer_safe_rewrite_plan |
| 3 | `/runtime-identifier-elimination-targets` | POST | runner_setuphelfer_runtime_identifier_elimination |
| 4 | `/runtime-identifier-elimination-plan` | POST | runner_setuphelfer_runtime_identifier_elimination |
| 5 | `/runtime-compatibility-alias-validation` | POST | runner_setuphelfer_runtime_identifier_elimination |
| 6 | `/runtime-identifier-patch-bump-preparation` | POST | runner_runtime_identifier_patch_bump_preparation |
| 7 | `/legacy-runtime-safe-migration-recommendations` | POST | runner_legacy_runtime_compatibility_validation |
| 8 | `/legacy-upgrade-path-matrix` | POST | runner_legacy_runtime_compatibility_validation |

## In routes.py verbleibend (versioning, nicht D.10)

- `/setuphelfer-controlled-rewrite-apply` (apply)
- cleanup-cycle plan/apply/postcheck (6 Routen)
- elimination apply/postcheck
- patch-bump apply/postcheck
- `/setuphelfer-branding-guard-check`

## Import-Reduktion

- `routes.py` Runner-Imports: 93 → **89** (−4 volle Import-Zeilen)
- Entfernte direkte Runner-Aufrufe: 8 Handler-Blöcke
