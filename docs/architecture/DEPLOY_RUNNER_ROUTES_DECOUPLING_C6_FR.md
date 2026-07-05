> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_RUNNER_ROUTES_DECOUPLING_C6_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Routes Decoupling C.6

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

Secours/USB/ISO execute, sudo, destructive, failure-execution-preview.

## C.7

Suivant allowed_plan_only slice or risk gate hardening.
