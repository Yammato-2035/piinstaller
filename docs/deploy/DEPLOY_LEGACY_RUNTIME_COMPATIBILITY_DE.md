# Deploy Legacy Runtime Compatibility (DE)

Read-only Kette zur Bewertung **bestehender pi-installer-Altinstallationen** neben **Setuphelfer**: Inventar aus Handoff-Daten, Koexistenz-Analyse, sichere Migrations**empfehlungen** (ohne Ausführung) und Upgrade-Pfad-Matrix.

**Eingaben:** `compatibility_aliases.json`, `runtime_identifier_zero_state_verification.json`, `setuphelfer_branding_guard_check.json`, `legacy_identifier_inventory.json`.

**Ausgaben (Handoff):**

1. `legacy_runtime_compatibility_inventory.json`
2. `legacy_runtime_coexistence_analysis.json`
3. `legacy_runtime_safe_migration_recommendations.json`
4. `legacy_upgrade_path_matrix.json`

**API (Reihenfolge empfohlen):**  
`POST /api/deploy/legacy-runtime-compatibility-inventory`  
`POST /api/deploy/legacy-runtime-coexistence-analysis`  
`POST /api/deploy/legacy-runtime-safe-migration-recommendations`  
`POST /api/deploy/legacy-upgrade-path-matrix`  

Codes jeweils `DEPLOY_LEGACY_RUNTIME_COMPATIBILITY_INVENTORY_*`, `DEPLOY_LEGACY_RUNTIME_COEXISTENCE_ANALYSIS_*`, `DEPLOY_LEGACY_RUNTIME_SAFE_MIGRATION_RECOMMENDATIONS_*`, `DEPLOY_LEGACY_UPGRADE_PATH_MATRIX_*` mit `OK` / `REVIEW_REQUIRED` / `BLOCKED`.

Keine echte Migration, kein systemctl, kein Löschen, kein Release/Publish — nur Analyse und strukturierte Evidence.
