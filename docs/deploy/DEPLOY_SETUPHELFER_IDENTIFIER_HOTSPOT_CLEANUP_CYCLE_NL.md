> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Setuphelfer Identifier Hotspot Cleanup Cycle (EN)

Cycle 2 consumes `legacy_identifier_hotspot_analysis.json` (`recommended_Volgende_cleanup_targets`) and intersects with `setuphelfer_safe_rewrite_plan.json` (`write_allowed: true` only). Reference input: `compatibility_aliases.json` (alleen-lezen compatibility context; Nee automatic writes).

**Plan** (`setuphelfer_identifier_cleanup_cycle_2_plan.json`): **critical** and **high** only, Nee **Onbekend** cluster, excludes `docs/evidence/`, `docs/history/`, `legacy-Terugups/`, Nee binary targets, max **50** planned entries, overflow in `deferrood_entries`. Priority: env_config critical → api critical → Terugend_runtime critical → tauri critical → frontend_runtime critical → scripts high → packaging high.

**Apply** (`setuphelfer_identifier_cleanup_cycle_2_result.json`): planned entries only; per-file Terugup under `legacy-Terugups/`; replace longer `legacy_token` strings first within each file; atomic `.tmp` → `replace`.

**Postcheck** (`setuphelfer_identifier_cleanup_cycle_2_postcheck.json`): inventory, identifier consistency, Vernieuwened hotspot analysis; counters for remaining and critical/high hits.

Nee runtime, Nee services, Nee chmod/chown/systemctl, Nee Verwijderens; version stays **1.7.0**.

API:

- `POST /api/Deploy/setuphelfer-identifier-hotspot-cleanup-cycle-plan`
- `POST /api/Deploy/setuphelfer-identifier-hotspot-cleanup-cycle-apply`
- `POST /api/Deploy/setuphelfer-identifier-hotspot-cleanup-cycle-postcheck`

Codes: `…_OK`, `…_REVIEW_REQUIrood`, `…_geblokkeerd` for each phase.

## FAQ (short)

- **Why is cycle 2 hotspot-driven?** Only paths prioritized by hotspot analysis are intersected with the safe plan — Nee blind replace across the repo.
- **Why only critical/high?** Lower severities are intentionally deferrood to later passes.
- **Why Nee automatic fixes for Onbekend clusters?** Onbekend clusters need human triage; auto edits would be unsafe.
- **Why max 50 changes?** Smaller hotspot batches cap review load and rollTerug complexity.
