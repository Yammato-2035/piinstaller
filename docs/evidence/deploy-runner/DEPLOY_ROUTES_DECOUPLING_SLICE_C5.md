# Deploy Routes Decoupling Slice (Phase C.5)

**HEAD-Basis:** `c299df3`

## Gewählter Slice (4 Routen)

| Route | Import entfernt | runner_id | Risiko (Gate) | C.5-Aktion |
|-------|-----------------|-----------|---------------|------------|
| `POST /runner/next-phase/gate` | `evaluate_runner_next_phase_gate` | `runner_next_phase_gate` | read_only / allowed_plan_only | Facade `build_plan_only_response` |
| `POST /version-governance/state` | `build_version_governance_state` | `runner_version_governance` | read_only / allowed_plan_only | Facade |
| `POST /version-source-of-truth-check` | `check_version_source_of_truth_consistency` | `runner_version_source_of_truth_check` | read_only / allowed_plan_only | Facade |
| `POST /legacy-identifier-inventory` | `build_legacy_identifier_inventory` | `runner_legacy_identifier_inventory` | read_only / allowed_plan_only | Facade |

## Response-Änderung (bewusst)

Payload enthält jetzt `facade_decoupling_c5: true`, `risk_gate`, `result` (Contract-Template). **Kein** Aufruf der Legacy-Runner-Funktion.

## Nicht migriert (Beispiele)

- `/runner/lab-phase/consolidation` — blocked_operator_required
- `/runner/release/readiness` — operator required
- `/execute`, `/write/*`, Rescue-Build — gefährlich
- 109 verbleibende direkte `runner_*`-Imports

## C.6

Nächster Slice: weitere `allowed_plan_only` / evidence_write Runner.
