# Deploy Evidence Router Slice (Phase D.7)

## Gewählte Routen (6 POST)

| Route | runner_id | Response-Key |
|---|---|---|
| `/legacy-identifier-cleanup-classification` | `runner_legacy_identifier_cleanup_classifier` | `legacy_identifier_cleanup_classification` |
| `/legacy-runtime-compatibility-inventory` | `runner_legacy_runtime_compatibility_validation` | `legacy_runtime_compatibility_inventory` |
| `/legacy-runtime-coexistence-analysis` | `runner_legacy_runtime_compatibility_validation` | `legacy_runtime_coexistence_analysis` |
| `/runner/manual-runtime/failure-test-results` | `runner_manual_runtime_failure_test_result_capture` | `capture` |
| `/runner/manual-runtime/failure-result-evaluation` | `runner_manual_runtime_failure_result_evaluation` | `evaluation` |
| `/runner/manual-runtime/result-validator-seal-consistency-audit` | `runner_manual_runtime_validator_seal_consistency_audit` | `audit` |

Alle mit `decoupling_phase="d7"`, `facade_decoupling_d7: true`, `allowed_to_execute: false`.

## Ausgeschlossene Routen (Auswahl)

| Route | Grund |
|---|---|
| `/rescue/*` evidence/inventory/manifest | Rescue-Domain — D.13+ |
| `*-apply`, `*-write`, `*-execute` | Write/Execute-Semantik |
| `/runner/manual-runtime/result-check` | `blocked_operator_required` |
| `/runner/manual-runtime/laptop-failure-*` | Slice-Limit (max 6) |

## Verbleibende Evidence-Routen in routes.py

Ca. 26 Evidence-nahe POST-Routen (Rescue, Manual-Runtime-Validator-Pipeline, Audit, Hardware-Gate) — unverändert.

## Import-Reduktion

- `routes.py` Runner-Imports: 103 → **99** (−4 Zeilen)
- Handler entfernt, Subrouter `routes_evidence.py` erweitert (6 → 12 Routen)
