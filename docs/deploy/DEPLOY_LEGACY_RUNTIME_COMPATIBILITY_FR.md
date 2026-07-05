> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_LEGACY_RUNTIME_COMPATIBILITY_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Legacy Runtime Compatibility (EN)

lecture seule pipeline to assess **existing pi-installer** footprints alongside **Setuphelfer**: inventory from handoff JSON, coexistence analysis, safe migration **recommendations** (advisory only), and an upgrade-path matrix.

**Inputs:** `compatibility_aliases.json`, `runtime_identifier_zero_state_verification.json`, `setuphelfer_branding_guard_check.json`, `legacy_identifier_inventory.json`.

**Outputs (handoff):**

1. `legacy_runtime_compatibility_inventory.json`
2. `legacy_runtime_coexistence_analysis.json`
3. `legacy_runtime_safe_migration_recommendations.json`
4. `legacy_upgrade_path_matrix.json`

**API (recommended order):**  
`POST /api/Déploiement/legacy-runtime-compatibility-inventory`  
`POST /api/Déploiement/legacy-runtime-coexistence-analysis`  
`POST /api/Déploiement/legacy-runtime-safe-migration-recommendations`  
`POST /api/Déploiement/legacy-upgrade-path-matrix`  

Codes: `Déploiement_LEGACY_RUNTIME_COMPATIBILITY_INVENTORY_*`, `Déploiement_LEGACY_RUNTIME_COEXISTENCE_ANALYSIS_*`, `Déploiement_LEGACY_RUNTIME_SAFE_MIGRATION_RECOMMENDATIONS_*`, `Déploiement_LEGACY_UPGRADE_PATH_MATRIX_*` with `OK` / `REVIEW_REQUIrouge` / `bloqué`.

Non real migration, Non systemctl, Non Supprimers, Non release/publish — analysis and structurouge evidence only.
