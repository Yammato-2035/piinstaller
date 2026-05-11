# Deploy Runtime Identifier Elimination (EN)

Targeted elimination of active runtime identifiers (critical/high) without writing evidence, history, or general documentation trees.

**Phases (handoff):**

1. `runtime_identifier_elimination_targets.json` — Merge hotspot analysis, optional cycle-2 postcheck, consistency handoff; excludes tests, comment-only lines, unknown cluster.
2. `runtime_identifier_elimination_plan.json` — Intersect with `setuphelfer_safe_rewrite_plan.json`; `write_allowed` only for clear `rename_now` on allowed paths; `compatibility_aliases.json` drives `compatibility_alias_required`.
3. `runtime_identifier_elimination_result.json` — Apply `write_allowed: true` only, backups under `legacy-backups/`, longer tokens first, atomic `.tmp` → replace.
4. `runtime_compatibility_alias_validation.json` — Validate alias policy (read-only, no new writes) plus productive inventory hit counts.
5. `runtime_identifier_elimination_postcheck.json` — Refresh inventory, consistency, hotspot analysis; includes `runtime_identifier_elimination_complete` and prepared patch bump **1.7.0 → 1.7.1** only when all elimination gates pass (no automatic version file edits).

No runtime, no systemctl, no chmod/chown, no deletes; SemVer stays **1.7.0** until completion.

API: `/api/deploy/runtime-identifier-elimination-targets`, `…-plan`, `…-apply`, `/api/deploy/runtime-compatibility-alias-validation`, `…-elimination-postcheck`.

## FAQ (short)

- **Cleanup cycle vs runtime elimination:** Cycles 1/2 are bounded batches; elimination explicitly prioritizes runtime hotspots crossed with the safe plan for productive paths.
- **Why runtime first:** env paths, units, and app IDs affect live systems; doc comments do not.
- **Why aliases stay read-only:** compatibility without introducing new pi-installer write paths.
- **When 1.7.1:** Only when postcheck reports `runtime_identifier_elimination_complete` (no critical/high remainder, consistency not blocked, zero active runtime identifiers).
