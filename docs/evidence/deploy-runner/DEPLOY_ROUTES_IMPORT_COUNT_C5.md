# Deploy Routes Import Count (Phase C.5)

| Metrik | Wert |
|--------|------|
| Direkte `from deploy.runner_*` **vorher** | **113** |
| Direkte `from deploy.runner_*` **nachher** | **109** |
| **Entfernt** | **4** |

## Entfernte Imports

1. `from deploy.runner_next_phase_gate import evaluate_runner_next_phase_gate`
2. `from deploy.runner_version_governance import build_version_governance_state`
3. `from deploy.runner_version_source_of_truth_check import check_version_source_of_truth_consistency`
4. `from deploy.runner_legacy_identifier_inventory import build_legacy_identifier_inventory`

## Verbleibend

109 direkte Runner-Imports — kein Big-Bang (Execute-/Rescue-/Write-Routen unverändert).

## Warum nicht alle 112?

Risk Gate blockiert die meisten Legacy-POST-Routen ohne Operator. Migration nur bei `allowed_plan_only` und dokumentierter Response-Änderung.
