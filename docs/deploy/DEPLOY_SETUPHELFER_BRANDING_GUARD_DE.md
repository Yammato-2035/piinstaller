# Deploy Setuphelfer Branding Guard (DE)

Read-only Schutz gegen die **Wiedereinführung** aktiver Legacy-Marken (`pi-installer`, `PI_INSTALLER_*`, alte Pfade/Services/App-IDs) nach der Migration zu **Setuphelfer**.

**Input:** `legacy_identifier_inventory.json`, `runtime_identifier_zero_state_verification.json`, `compatibility_aliases.json`, `config/version.json`.

**Output:** `docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json`

**API:** `POST /api/deploy/setuphelfer-branding-guard-check` mit Codes `DEPLOY_SETUPHELFER_BRANDING_GUARD_CHECK_{OK|REVIEW_REQUIRED|BLOCKED}`.

**Skript (lokal, optional):** `scripts/check-setuphelfer-branding-guard.sh` — nur Suche, keine Dateiänderungen, kein Hook-Install.

Kein Rewrite, keine Runtime-Ausführung, keine Service-Manipulation, kein Release/Tag/Publish.

**Version:** Kein neuer Minor-Bump; mit grünem Zero-State und grünem Branding-Guard bleibt **1.7.1** konsistent; bei Blockierung keine Freigabe.

Siehe auch: `docs/developer/SETUPHELFER_BRANDING_GUARD.md`.
