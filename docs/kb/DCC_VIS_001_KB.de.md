# KB — DCC-VIS-001 Runtime-Statusmodell (de)

## Komponenten

| Datei | Rolle |
|-------|-------|
| `runtimeStatusModel.ts` | 5-Achsen-Modell |
| `loadDevDashboard.ts` | `localApiReachable` |
| `governanceMatrix.ts` | Alerts ohne Fake-Offline |

## Operator-Checkliste

1. `curl -s http://127.0.0.1:8000/health`
2. `curl -s http://127.0.0.1:8000/api/version`
3. Developer Token im DCC speichern und prüfen
4. `./scripts/check-runtime-deploy-gate.sh` (Phase 0)

## Evidence

`docs/evidence/DCC_VIS_001_RUNTIME_GATE_STATUS_MODEL.md`
