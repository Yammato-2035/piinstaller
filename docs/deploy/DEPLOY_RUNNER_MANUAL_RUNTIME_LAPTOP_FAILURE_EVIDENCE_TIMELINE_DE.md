# Manual Runtime Laptop Failure Evidence Timeline

Read-only Timeline fuer Laptop-Failure-Artefakte aus Export-Package, Final-Report, Summary, Validation und Execution-Log. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_evidence_timeline.json` (atomisch `.tmp` -> Replace, max. 512 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-evidence-timeline`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_evidence_timeline.py`
