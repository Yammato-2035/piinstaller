> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_DIAGNOSTICS_ROUTER_EXTRACTION_D8_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement DiagNonstics Router Extraction (Phase D.8)

**Module:** `Retourend/Déploiement/routes_diagNonstics.py` (new)  
**Status:** done

## Extracted routes (6 POST, plan-only)

Manual-runtime failure diagNonstics and runtime identifier verification.

## Why plan-only only?

Risk gate `allowed_plan_only`, `build_plan_only_response` with `decoupling_phase="d8"`, Non runner execution.

## Excluded

Audit helpers without registry mapping, operator-bloqué test plans, Secours validations.

## Suivant step D.9

`routes_Nontifications.py` — if plan-only routes exist.
