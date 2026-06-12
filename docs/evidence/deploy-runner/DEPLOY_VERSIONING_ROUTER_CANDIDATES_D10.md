# Deploy Versioning Router Candidates (D.10)

**HEAD:** `4db68db` (vor D.10) · **Module-Reuse:** M.1 geprüft

## Suchkriterien

version, identifier, source-of-truth, consistency, compatibility, zero-state, legacy-identifier, setuphelfer-identifier

## Pflichttabelle

| Route | runner_id | risk_level | execution_policy | C.4 Decision | Apply/Rewrite? | D.10 geeignet | Grund |
| ----- | --------- | ---------- | ---------------- | ------------ | -------------- | ------------- | ----- |
| POST `/version-governance/state` | runner_version_governance | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **nein** | bereits D.5 `routes_governance.py` |
| POST `/version-source-of-truth-check` | runner_version_source_of_truth_check | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **nein** | bereits D.5 |
| POST `/legacy-identifier-inventory` | runner_legacy_identifier_inventory | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **nein** | bereits D.4/D.7 evidence |
| POST `/setuphelfer-identifier-consistency-check` | runner_setuphelfer_identifier_consistency_check | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **nein** | bereits evidence |
| POST `/runtime-identifier-zero-state-verification` | runner_runtime_identifier_zero_state_verification | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **nein** | bereits D.8 diagnostics |
| POST `/setuphelfer-runtime-identifier-migration` | runner_setuphelfer_runtime_identifier_migration | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | plan-only, facade-decouplable |
| POST `/setuphelfer-safe-rewrite-plan` | runner_setuphelfer_safe_rewrite_plan | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | plan-only (nicht apply) |
| POST `/setuphelfer-controlled-rewrite-apply` | — | system_change | — | BLOCKED | **ja** | **nein** | apply ausgeschlossen |
| POST `/setuphelfer-identifier-cleanup-cycle-plan` | runner_setuphelfer_identifier_cleanup_cycle | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **später** | plan ok, Slice voll |
| POST `/setuphelfer-identifier-cleanup-cycle-apply` | — | system_change | — | BLOCKED | **ja** | **nein** | apply |
| POST `/runtime-identifier-elimination-targets` | runner_setuphelfer_runtime_identifier_elimination | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | read/plan |
| POST `/runtime-identifier-elimination-plan` | runner_setuphelfer_runtime_identifier_elimination | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | plan |
| POST `/runtime-identifier-elimination-apply` | — | system_change | — | BLOCKED | **ja** | **nein** | apply |
| POST `/runtime-compatibility-alias-validation` | runner_setuphelfer_runtime_identifier_elimination | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | validation only |
| POST `/runtime-identifier-patch-bump-preparation` | runner_runtime_identifier_patch_bump_preparation | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | preparation only |
| POST `/runtime-identifier-patch-bump-apply` | runner_runtime_identifier_patch_bump_apply | system_change | — | BLOCKED | **ja** | **nein** | apply |
| POST `/legacy-runtime-safe-migration-recommendations` | runner_legacy_runtime_compatibility_validation | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | recommendations |
| POST `/legacy-upgrade-path-matrix` | runner_legacy_runtime_compatibility_validation | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | matrix read |
| POST `/setuphelfer-branding-guard-check` | runner_setuphelfer_branding_guard | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **später** | Slice voll (max 8) |
| POST `/runner/install/consistency` | runner_install_consistency | read_only | lab_only | ALLOWED_PLAN_ONLY | nein | **nein** | nicht versioning-Domäne |

## Ausgeschlossen (explizit)

Alle `*-apply`, `*-rewrite-apply`, `execute`, `write`, `install`, `delete` Routen in `routes.py`.
