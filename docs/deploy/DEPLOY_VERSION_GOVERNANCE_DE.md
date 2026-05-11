# Deploy Version Governance

Read-only Version-Governance fuer STRICT-Mode-Phasen. SemVer-Bump wird aus Aenderungstypen abgeleitet und als `version_state.json` dokumentiert.

API: `POST /api/deploy/version-governance/state`

Codes: `DEPLOY_VERSION_GOVERNANCE_STATE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_version_governance.py`, `backend/deploy/runner_version_consistency_check.py`
