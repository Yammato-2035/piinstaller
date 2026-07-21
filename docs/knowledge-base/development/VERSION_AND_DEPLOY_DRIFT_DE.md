# Version & Deploy-Drift (KB)

**Task:** PI-RS-BVR-GUI-DCC-001

## Source of Truth

- `config/version.json` → `project_version`
- `config/rescue_payload_version.json` → `rescue_payload_version`
- Deploy-Manifeste (Workspace + `/opt/setuphelfer`)

## Ampeln

| Farbe | Bedeutung |
|-------|-----------|
| GREEN | Identitäten stimmen |
| YELLOW | Dokumentierter Lag (Feature vs. main, GUI-Fallback) |
| RED | Unerwartete Abweichung |
| GRAY | Unbekannt — **nicht** als OK werten |

## Drift-Typen

`workspace_runtime_commit_drift`, `workspace_runtime_version_drift`, `backend_frontend_version_drift`, `payload_usb_version_drift`, `payload_usb_sha256_drift`, `unknown_runtime_identity`.

## Phase 0

```bash
./scripts/check-runtime-deploy-gate.sh
python3 backend/tools/check_version_consistency.py --repo-root .
```

Exit 17/18/19 = blockiert.

## Siehe auch

- [VERSION_COMMIT_DRIFT_CONTRACT.md](../../architecture/VERSION_COMMIT_DRIFT_CONTRACT.md)
- [RUNTIME_DEPLOY_AND_DRIFT_RUNBOOK.md](../../operator/RUNTIME_DEPLOY_AND_DRIFT_RUNBOOK.md)
