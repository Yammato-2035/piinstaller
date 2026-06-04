# Runtime Governance — Characterization Tests

**Datei:** `backend/tests/test_runtime_governance_*.py`

| Contract | Abgedeckt |
|----------|-----------|
| `release` — dev_control off, devserver off, routes blocked | `test_runtime_governance_profile_policy_v1`, `route_exposure` |
| `local_lab` — dev_control on, devserver on, require_token false | `devserver_policy`, `no_profile_desync` |
| Runtime Ports in Snapshot | `test_runtime_governance_snapshot_v1` |
| `/api/version` Felder kompatibel | snapshot + parity |
| Route release vs local_lab | `route_exposure` |
| Keine Profil-Desync | `no_profile_desync` |
| Parity Legacy vs Governance | `parity_v1` (5 Profile) |
| Module boundaries | `module_boundaries_v1` |

**Ergebnis:** 13 passed (`backend/venv/bin/python3 -m pytest`).
