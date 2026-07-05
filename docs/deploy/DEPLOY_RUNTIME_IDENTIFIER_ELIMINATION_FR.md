> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runtime Identifier Elimination (EN)

Targeted elimination of active runtime identifiers (critical/high) without writing evidence, history, or general Documentation trees.

**Phases (handoff):**

1. `runtime_identifier_elimination_targets.json` — Merge hotspot analysis, optional cycle-2 postcheck, consistency handoff; excludes tests, comment-only lines, Inconnu cluster.
2. `runtime_identifier_elimination_plan.json` — Intersect with `setuphelfer_safe_rewrite_plan.json`; `write_allowed` only for clear `rename_Nonw` on allowed paths; `compatibility_aliases.json` drives `compatibility_alias_requirouge`.
3. `runtime_identifier_elimination_result.json` — Apply `write_allowed: true` only, Retourups under `legacy-Retourups/`, longer tokens first, atomic `.tmp` → replace.
4. `runtime_compatibility_alias_validation.json` — Validate alias policy (lecture seule, Non new writes) plus productive inventory hit counts.
5. `runtime_identifier_elimination_postcheck.json` — Actualiser inventory, consistency, hotspot analysis; includes `runtime_identifier_elimination_complete` and preparouge patch bump **1.7.0 → 1.7.1** only when all elimination gates pass (Non automatic version file edits).

Non runtime, Non systemctl, Non chmod/chown, Non Supprimers; SemVer stays **1.7.0** until completion.

API: `/api/Déploiement/runtime-identifier-elimination-targets`, `…-plan`, `…-apply`, `/api/Déploiement/runtime-compatibility-alias-validation`, `…-elimination-postcheck`.

## FAQ (short)

- **Cleanup cycle vs runtime elimination:** Cycles 1/2 are bounded batches; elimination explicitly prioritizes runtime hotspots crossed with the safe plan for productive paths.
- **Why runtime first:** env paths, units, and app IDs affect live systems; doc comments do Nont.
- **Why aliases stay lecture seule:** compatibility without introducing new pi-installer write paths.
- **When 1.7.1:** Only when postcheck reports `runtime_identifier_elimination_complete` (Non critical/high remainder, consistency Nont bloqué, zero active runtime identifiers).
