# Deploy Runner Routes Decoupling C.6

**Second slice** — 5 evidence_write / allowed_plan_only routes decoupled.

## Migrated routes

- `/legacy-identifier-hotspot-analysis`
- `/setuphelfer-identifier-consistency-check`
- `/runner/manual-runtime/evidence-timeline`
- `/runner/manual-runtime/evidence-final-snapshot`
- `/runner/manual-runtime/result-validator-seal-index`

## Imports

113 → 104 (C.5+C.6: −9). `allowed_to_execute` stays **false**.

## Excluded

Rescue/USB/ISO execute, sudo, destructive, failure-execution-preview.

## C.7

Next allowed_plan_only slice or risk gate hardening.
