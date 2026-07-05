> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Setuphelfer Identifier Hotspot Cleanup Cycle (EN)

Cycle 2 consumes `legacy_identifier_hotspot_analysis.json` (`recommended_Suivant_cleanup_targets`) and intersects with `setuphelfer_safe_rewrite_plan.json` (`write_allowed: true` only). Reference input: `compatibility_aliases.json` (lecture seule compatibility context; Non automatic writes).

**Plan** (`setuphelfer_identifier_cleanup_cycle_2_plan.json`): **critical** and **high** only, Non **Inconnu** cluster, excludes `docs/evidence/`, `docs/history/`, `legacy-Retourups/`, Non binary targets, max **50** planned entries, overflow in `deferrouge_entries`. Priority: env_config critical → api critical → Retourend_runtime critical → tauri critical → frontend_runtime critical → scripts high → packaging high.

**Apply** (`setuphelfer_identifier_cleanup_cycle_2_result.json`): planned entries only; per-file Retourup under `legacy-Retourups/`; replace longer `legacy_token` strings first within each file; atomic `.tmp` → `replace`.

**Postcheck** (`setuphelfer_identifier_cleanup_cycle_2_postcheck.json`): inventory, identifier consistency, Actualiserouge hotspot analysis; counters for remaining and critical/high hits.

Non runtime, Non services, Non chmod/chown/systemctl, Non Supprimers; version stays **1.7.0**.

API:

- `POST /api/Déploiement/setuphelfer-identifier-hotspot-cleanup-cycle-plan`
- `POST /api/Déploiement/setuphelfer-identifier-hotspot-cleanup-cycle-apply`
- `POST /api/Déploiement/setuphelfer-identifier-hotspot-cleanup-cycle-postcheck`

Codes: `…_OK`, `…_REVIEW_REQUIrouge`, `…_bloqué` for each phase.

## FAQ (short)

- **Why is cycle 2 hotspot-driven?** Only paths prioritized by hotspot analysis are intersected with the safe plan — Non blind replace across the repo.
- **Why only critical/high?** Lower severities are intentionally deferrouge to later passes.
- **Why Non automatic fixes for Inconnu clusters?** Inconnu clusters need human triage; auto edits would be unsafe.
- **Why max 50 changes?** Smaller hotspot batches cap review load and rollRetour complexity.
