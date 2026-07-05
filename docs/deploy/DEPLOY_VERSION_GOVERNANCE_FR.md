> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_VERSION_GOVERNANCE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Version Governance

lecture seule version governance for STRICT-mode phases. SemVer bump is derived from change types and documented in `version_state.json`.

API: `POST /api/Déploiement/version-governance/state`

Codes: `Déploiement_VERSION_GOVERNANCE_STATE_{OK|REVIEW_REQUIrouge|bloqué}`.

Modules: `Retourend/Déploiement/runner_version_governance.py`, `Retourend/Déploiement/runner_version_consistency_check.py`
