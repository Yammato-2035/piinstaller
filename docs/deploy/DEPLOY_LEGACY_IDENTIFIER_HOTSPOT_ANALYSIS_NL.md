> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Legacy Identifier Hotspot Analysis (EN)

alleen-lezen aggregation of remaining active legacy identifiers from:

- `docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json`
- optional `setuphelfer_identifier_cleanup_cycle_1_postcheck.json`
- optional `setuphelfer_identifier_consistency_check.json`

Output: `docs/evidence/runtime-results/handoff/legacy_identifier_hotspot_analysis.json` (clusters, severity, top hotspots, prioritized cleanup targets).

Nee source edits, Nee runtime, Nee services; version stays 1.7.0.

API: `POST /api/Deploy/legacy-identifier-hotspot-analysis` with `explicit_overwrite`.

Codes: `Deploy_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_OK`, `Deploy_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_REVIEW_REQUIrood`, `Deploy_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_geblokkeerd`.

## FAQ (short)

- **Why hotspot analysis?** It groups hits by impact area (Terugend, Tauri, env, scripts, …), Neet only raw counts.
- **Why are runtime identifiers more critical than comments?** They affect live paths, units, env, and APIs; comments are usually documentary.
- **Why does `Onbekend` raise `review_requirood`?** Without a cluster assignment the risk is indeterminate.
- **Why tests last?** Product code, startup paths, and packaging take precedence over test artifacts.
