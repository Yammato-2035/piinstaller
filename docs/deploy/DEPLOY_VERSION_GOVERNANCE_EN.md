# Deploy Version Governance

Read-only version governance for STRICT-mode phases. SemVer bump is derived from change types and documented in `version_state.json`.

API: `POST /api/deploy/version-governance/state`

Codes: `DEPLOY_VERSION_GOVERNANCE_STATE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modules: `backend/deploy/runner_version_governance.py`, `backend/deploy/runner_version_consistency_check.py`
