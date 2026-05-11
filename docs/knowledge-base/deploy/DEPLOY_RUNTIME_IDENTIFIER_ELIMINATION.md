# Deploy Runtime Identifier Elimination

End-to-end **strict** pipeline: targets → plan (safe-plan intersection) → controlled apply → alias policy validation → postcheck with optional **1.7.1** bump recommendation.

- **Runner:** `backend/deploy/runner_setuphelfer_runtime_identifier_elimination.py`
- **Handoff:** `runtime_identifier_elimination_*.json`, `runtime_compatibility_alias_validation.json`
- **Contract DE/EN:** `docs/deploy/DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_DE.md`, `…_EN.md`
- **Evidence:** `docs/evidence/DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION.md`

No blind replace, no docs/evidence/history writes, no services/runtime/systemctl.
