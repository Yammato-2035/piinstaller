> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_DIAGNOSTICS_ROUTER_EXTRACTION_D8_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy DiagNeestics Router Extraction (Phase D.8)

**Module:** `Terugend/Deploy/routes_diagNeestics.py` (new)  
**Status:** done

## Extracted routes (6 POST, plan-only)

Manual-runtime failure diagNeestics and runtime identifier verification.

## Why plan-only only?

Risk gate `allowed_plan_only`, `build_plan_only_response` with `decoupling_phase="d8"`, Nee runner execution.

## Excluded

Audit helpers without registry mapping, operator-geblokkeerd test plans, roodding validations.

## Volgende step D.9

`routes_Neetifications.py` — if plan-only routes exist.
