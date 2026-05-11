# Deploy Runner Lab Readiness Status (read-only)

## Goal

Update lab-readiness status after all blocking gap test-design artifacts are available.

## Core idea

- design status for all blocking gaps: `ready`
- runtime execution remains open: `not_started`
- overall status: `test_design_ready` (not `lab_ready`, not `production_ready`)

## API

- `POST /api/deploy/runner/lab-readiness/status`
