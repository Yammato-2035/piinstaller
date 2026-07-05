# KB — DCC-VIS-001 runtime status model (en)

## Components

| File | Role |
|------|------|
| `runtimeStatusModel.ts` | 5-axis model |
| `loadDevDashboard.ts` | `localApiReachable` |
| `governanceMatrix.ts` | alerts without fake offline |

## Operator checklist

1. `curl -s http://127.0.0.1:8000/health`
2. `curl -s http://127.0.0.1:8000/api/version`
3. Save and verify developer token in DCC
4. `./scripts/check-runtime-deploy-gate.sh` (Phase 0)

## Evidence

`docs/evidence/DCC_VIS_001_RUNTIME_GATE_STATUS_MODEL.md`
