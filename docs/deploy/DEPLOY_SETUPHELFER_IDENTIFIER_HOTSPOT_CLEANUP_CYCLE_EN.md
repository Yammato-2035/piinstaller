# Deploy Setuphelfer Identifier Hotspot Cleanup Cycle (EN)

Cycle 2 consumes `legacy_identifier_hotspot_analysis.json` (`recommended_next_cleanup_targets`) and intersects with `setuphelfer_safe_rewrite_plan.json` (`write_allowed: true` only). Reference input: `compatibility_aliases.json` (read-only compatibility context; no automatic writes).

**Plan** (`setuphelfer_identifier_cleanup_cycle_2_plan.json`): **critical** and **high** only, no **unknown** cluster, excludes `docs/evidence/`, `docs/history/`, `legacy-backups/`, no binary targets, max **50** planned entries, overflow in `deferred_entries`. Priority: env_config critical → api critical → backend_runtime critical → tauri critical → frontend_runtime critical → scripts high → packaging high.

**Apply** (`setuphelfer_identifier_cleanup_cycle_2_result.json`): planned entries only; per-file backup under `legacy-backups/`; replace longer `legacy_token` strings first within each file; atomic `.tmp` → `replace`.

**Postcheck** (`setuphelfer_identifier_cleanup_cycle_2_postcheck.json`): inventory, identifier consistency, refreshed hotspot analysis; counters for remaining and critical/high hits.

No runtime, no services, no chmod/chown/systemctl, no deletes; version stays **1.7.0**.

API:

- `POST /api/deploy/setuphelfer-identifier-hotspot-cleanup-cycle-plan`
- `POST /api/deploy/setuphelfer-identifier-hotspot-cleanup-cycle-apply`
- `POST /api/deploy/setuphelfer-identifier-hotspot-cleanup-cycle-postcheck`

Codes: `…_OK`, `…_REVIEW_REQUIRED`, `…_BLOCKED` for each phase.

## FAQ (short)

- **Why is cycle 2 hotspot-driven?** Only paths prioritized by hotspot analysis are intersected with the safe plan — no blind replace across the repo.
- **Why only critical/high?** Lower severities are intentionally deferred to later passes.
- **Why no automatic fixes for unknown clusters?** Unknown clusters need human triage; auto edits would be unsafe.
- **Why max 50 changes?** Smaller hotspot batches cap review load and rollback complexity.
