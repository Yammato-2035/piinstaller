# Deploy Legacy Identifier Hotspot Analysis (EN)

Read-only aggregation of remaining active legacy identifiers from:

- `docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json`
- optional `setuphelfer_identifier_cleanup_cycle_1_postcheck.json`
- optional `setuphelfer_identifier_consistency_check.json`

Output: `docs/evidence/runtime-results/handoff/legacy_identifier_hotspot_analysis.json` (clusters, severity, top hotspots, prioritized cleanup targets).

No source edits, no runtime, no services; version stays 1.7.0.

API: `POST /api/deploy/legacy-identifier-hotspot-analysis` with `explicit_overwrite`.

Codes: `DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_OK`, `DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_REVIEW_REQUIRED`, `DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_BLOCKED`.

## FAQ (short)

- **Why hotspot analysis?** It groups hits by impact area (backend, Tauri, env, scripts, …), not only raw counts.
- **Why are runtime identifiers more critical than comments?** They affect live paths, units, env, and APIs; comments are usually documentary.
- **Why does `unknown` raise `review_required`?** Without a cluster assignment the risk is indeterminate.
- **Why tests last?** Product code, startup paths, and packaging take precedence over test artifacts.
