# Deploy Runner Routes Decoupling C.6

**Zweiter Slice** — 5 evidence_write / allowed_plan_only Routen decoupled.

## Migrierte Routen

- `/legacy-identifier-hotspot-analysis`
- `/setuphelfer-identifier-consistency-check`
- `/runner/manual-runtime/evidence-timeline`
- `/runner/manual-runtime/evidence-final-snapshot`
- `/runner/manual-runtime/result-validator-seal-index`

## Imports

113 → 104 (C.5+C.6: −9). `allowed_to_execute` bleibt **false**.

## Ausgeschlossen

Rescue/USB/ISO-Execute, sudo, destructive, failure-execution-preview.

## C.7

Nächster allowed_plan_only-Slice oder Risk-Gate-Verschärfung.
