# Deploy Runtime Identifier Zero State Verification

Aggregates **elimination postcheck**, **alias validation**, **identifier consistency handoff**, **inventory**, **hotspot analysis**, and **`config/version.json`** to decide `ok` / `review_required` / `blocked` for runtime-legacy zero state.

- **Runner:** `backend/deploy/runner_runtime_identifier_zero_state_verification.py` (`verify_runtime_identifier_zero_state`)
- **Patch prep:** `backend/deploy/runner_runtime_identifier_patch_bump_preparation.py`
- **Patch apply/postcheck:** `backend/deploy/runner_runtime_identifier_patch_bump_apply.py`
- **Contract DE/EN:** `docs/deploy/DEPLOY_RUNTIME_IDENTIFIER_ZERO_STATE_VERIFICATION_DE.md`, `…_EN.md`
- **Evidence:** `docs/evidence/DEPLOY_RUNTIME_IDENTIFIER_ZERO_STATE_VERIFICATION.md`

No automatic version file edits until explicit patch-bump apply with all gates green.
