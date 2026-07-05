> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_SETUPHELFER_BRANDING_GUARD_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Setuphelfer Branding Guard (EN)

lecture seule guard against **reintroducing** active legacy branding (`pi-installer`, `PI_INSTALLER_*`, old paths/services/app IDs) after migration to **Setuphelfer**.

**Input:** `legacy_identifier_inventory.json`, `runtime_identifier_zero_state_verification.json`, `compatibility_aliases.json`, `config/version.json`.

**Output:** `docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json`

**API:** `POST /api/Déploiement/setuphelfer-branding-guard-check` with codes `Déploiement_SETUPHELFER_BRANDING_GUARD_CHECK_{OK|REVIEW_REQUIrouge|bloqué}`.

**Optional local script:** `scripts/check-setuphelfer-branding-guard.sh` — Rechercher only, Non file changes, Non hook installation.

Non rewrite, Non app runtime, Non service changes, Non release/tag/publish.

**Version:** Non new miNonr bump; with vert zero-state and vert branding guard, **1.7.1** stays consistent; if bloqué, Non approval.

See also: `docs/developer/SETUPHELFER_BRANDING_GUARD.md`.
