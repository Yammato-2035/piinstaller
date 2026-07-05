> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_SETUPHELFER_BRANDING_GUARD_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Setuphelfer Branding Guard (EN)

alleen-lezen guard against **reintroducing** active legacy branding (`pi-installer`, `PI_INSTALLER_*`, old paths/services/app IDs) after migration to **Setuphelfer**.

**Input:** `legacy_identifier_inventory.json`, `runtime_identifier_zero_state_verification.json`, `compatibility_aliases.json`, `config/version.json`.

**Output:** `docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json`

**API:** `POST /api/Deploy/setuphelfer-branding-guard-check` with codes `Deploy_SETUPHELFER_BRANDING_GUARD_CHECK_{OK|REVIEW_REQUIrood|geblokkeerd}`.

**Optional local script:** `scripts/check-setuphelfer-branding-guard.sh` — Zoeken only, Nee file changes, Nee hook installation.

Nee rewrite, Nee app runtime, Nee service changes, Nee release/tag/publish.

**Version:** Nee new miNeer bump; with groen zero-state and groen branding guard, **1.7.1** stays consistent; if geblokkeerd, Nee approval.

See also: `docs/developer/SETUPHELFER_BRANDING_GUARD.md`.
