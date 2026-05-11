# Deploy Setuphelfer Branding Guard (EN)

Read-only guard against **reintroducing** active legacy branding (`pi-installer`, `PI_INSTALLER_*`, old paths/services/app IDs) after migration to **Setuphelfer**.

**Input:** `legacy_identifier_inventory.json`, `runtime_identifier_zero_state_verification.json`, `compatibility_aliases.json`, `config/version.json`.

**Output:** `docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json`

**API:** `POST /api/deploy/setuphelfer-branding-guard-check` with codes `DEPLOY_SETUPHELFER_BRANDING_GUARD_CHECK_{OK|REVIEW_REQUIRED|BLOCKED}`.

**Optional local script:** `scripts/check-setuphelfer-branding-guard.sh` — search only, no file changes, no hook installation.

No rewrite, no app runtime, no service changes, no release/tag/publish.

**Version:** No new minor bump; with green zero-state and green branding guard, **1.7.1** stays consistent; if blocked, no approval.

See also: `docs/developer/SETUPHELFER_BRANDING_GUARD.md`.
