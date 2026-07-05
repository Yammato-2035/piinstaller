> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Legacy Identifier Hotspot Analysis (EN)

lecture seule aggregation of remaining active legacy identifiers from:

- `docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json`
- optional `setuphelfer_identifier_cleanup_cycle_1_postcheck.json`
- optional `setuphelfer_identifier_consistency_check.json`

Output: `docs/evidence/runtime-results/handoff/legacy_identifier_hotspot_analysis.json` (clusters, severity, top hotspots, prioritized cleanup targets).

Non source edits, Non runtime, Non services; version stays 1.7.0.

API: `POST /api/Déploiement/legacy-identifier-hotspot-analysis` with `explicit_overwrite`.

Codes: `Déploiement_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_OK`, `Déploiement_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_REVIEW_REQUIrouge`, `Déploiement_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_bloqué`.

## FAQ (short)

- **Why hotspot analysis?** It groups hits by impact area (Retourend, Tauri, env, scripts, …), Nont only raw counts.
- **Why are runtime identifiers more critical than comments?** They affect live paths, units, env, and APIs; comments are usually documentary.
- **Why does `Inconnu` raise `review_requirouge`?** Without a cluster assignment the risk is indeterminate.
- **Why tests last?** Product code, startup paths, and packaging take precedence over test artifacts.
