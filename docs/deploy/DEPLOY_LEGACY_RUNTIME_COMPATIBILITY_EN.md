# Deploy Legacy Runtime Compatibility (EN)

Read-only pipeline to assess **existing pi-installer** footprints alongside **Setuphelfer**: inventory from handoff JSON, coexistence analysis, safe migration **recommendations** (advisory only), and an upgrade-path matrix.

**Inputs:** `compatibility_aliases.json`, `runtime_identifier_zero_state_verification.json`, `setuphelfer_branding_guard_check.json`, `legacy_identifier_inventory.json`.

**Outputs (handoff):**

1. `legacy_runtime_compatibility_inventory.json`
2. `legacy_runtime_coexistence_analysis.json`
3. `legacy_runtime_safe_migration_recommendations.json`
4. `legacy_upgrade_path_matrix.json`

**API (recommended order):**  
`POST /api/deploy/legacy-runtime-compatibility-inventory`  
`POST /api/deploy/legacy-runtime-coexistence-analysis`  
`POST /api/deploy/legacy-runtime-safe-migration-recommendations`  
`POST /api/deploy/legacy-upgrade-path-matrix`  

Codes: `DEPLOY_LEGACY_RUNTIME_COMPATIBILITY_INVENTORY_*`, `DEPLOY_LEGACY_RUNTIME_COEXISTENCE_ANALYSIS_*`, `DEPLOY_LEGACY_RUNTIME_SAFE_MIGRATION_RECOMMENDATIONS_*`, `DEPLOY_LEGACY_UPGRADE_PATH_MATRIX_*` with `OK` / `REVIEW_REQUIRED` / `BLOCKED`.

No real migration, no systemctl, no deletes, no release/publish — analysis and structured evidence only.
