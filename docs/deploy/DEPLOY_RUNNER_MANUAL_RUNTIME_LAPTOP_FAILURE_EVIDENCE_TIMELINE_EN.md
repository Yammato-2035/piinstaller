# Manual Runtime Laptop Failure Evidence Timeline

Read-only timeline for laptop failure artifacts from export package, final report, summary, validation, and execution log. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_evidence_timeline.json` (atomic `.tmp` -> replace, max 512 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-evidence-timeline`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_evidence_timeline.py`
