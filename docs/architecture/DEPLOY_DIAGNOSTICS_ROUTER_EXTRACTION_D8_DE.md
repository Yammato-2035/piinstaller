> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/DEPLOY_DIAGNOSTICS_ROUTER_EXTRACTION_D8_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Diagnostik Router Extraktion (Phase D.8)

**Module:** `backend/deploy/routes_diagnostics.py` (new)  
**Stand:** done

## Extracted routes (6 POST, plan-only)

Manual-runtime failure diagnostics and runtime identifier verification.

## Why plan-only only?

Risk gate `allowed_plan_only`, `build_plan_only_response` with `decoupling_phase="d8"`, no runner execution.

## Excluded

Audit helpers without registry mapping, operator-blocked test plans, rescue validations.

## Next step D.9

`routes_notifications.py` — if plan-only routes exist.
