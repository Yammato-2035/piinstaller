# Version & Deploy Drift (KB)

**Task:** PI-RS-BVR-GUI-DCC-001

## Source of truth

- `config/version.json` → `project_version`
- `config/rescue_payload_version.json` → `rescue_payload_version`
- Deploy manifests (workspace + `/opt/setuphelfer`)

## Traffic lights

| Color | Meaning |
|-------|---------|
| GREEN | Identities match |
| YELLOW | Documented lag (feature vs. main, GUI fallback) |
| RED | Unexpected mismatch |
| GRAY | Unknown — **do not** treat as OK |

## Drift types

`workspace_runtime_commit_drift`, `workspace_runtime_version_drift`, `backend_frontend_version_drift`, `payload_usb_version_drift`, `payload_usb_sha256_drift`, `unknown_runtime_identity`.

## Phase 0

```bash
./scripts/check-runtime-deploy-gate.sh
python3 backend/tools/check_version_consistency.py --repo-root .
```

Exit 17/18/19 = blocked.

## See also

- [VERSION_COMMIT_DRIFT_CONTRACT.md](../../architecture/VERSION_COMMIT_DRIFT_CONTRACT.md)
- [RUNTIME_DEPLOY_AND_DRIFT_RUNBOOK.md](../../operator/RUNTIME_DEPLOY_AND_DRIFT_RUNBOOK.md)
