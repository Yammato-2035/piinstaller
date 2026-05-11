# Deploy Setuphelfer Identifier Hotspot Cleanup Cycle

Cycle **2** complements the generic cleanup cycle (max. 100) by driving work from **`legacy_identifier_hotspot_analysis.json`** recommendations crossed with **`setuphelfer_safe_rewrite_plan.json`**.

- **Runner:** `backend/deploy/runner_setuphelfer_identifier_hotspot_cleanup_cycle.py`
- **Handoff:** `setuphelfer_identifier_cleanup_cycle_2_plan.json`, `_result.json`, `_postcheck.json`
- **Contract DE/EN:** `docs/deploy/DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_DE.md`, `…_EN.md`
- **Evidence index:** `docs/evidence/DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE.md`

Strict: no evidence/history edits, no services/runtime, max **50** planned writes, longer tokens first per file, backups under `legacy-backups/`.
