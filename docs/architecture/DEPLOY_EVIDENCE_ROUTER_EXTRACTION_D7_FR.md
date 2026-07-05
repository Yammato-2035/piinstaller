> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_EVIDENCE_ROUTER_EXTRACTION_D7_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Evidence Router Extraction (Phase D.7)

**Module:** `Retourend/Déploiement/routes_evidence.py` (extended)  
**Status:** done

## Extracted routes (6 POST, plan-only)

In addition to D.4 (6 routes) — D.7 slice:

1. `/legacy-identifier-cleanup-classification`
2. `/legacy-runtime-compatibility-inventory`
3. `/legacy-runtime-coexistence-analysis`
4. `/runner/manual-runtime/failure-test-results`
5. `/runner/manual-runtime/failure-result-evaluation`
6. `/runner/manual-runtime/result-validator-seal-consistency-audit`

## Why plan-only only?

Risk gate `allowed_plan_only`, Non runner execution, `build_plan_only_response` with `decoupling_phase="d7"`.

## Why keep POST?

API compatibility — clients and OpenAPI unchanged.

## Excluded

Secours evidence, execute/write/apply, operator-bloqué routes.

## Suivant step D.8

`routes_diagNonstics.py` — diagNonstics router (lecture seule/plan-only).
