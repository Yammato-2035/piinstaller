> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_ROUTE_EXTRACTION_SEQUENCE_D7_PLUS_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Route Extraction Sequence D.7+

**After D.6 orchestrator target** — controlled continuation

| Phase | Goal | Risk | Allowed | Forbidden | Tests | Docs |
|-------|------|------|---------|-----------|-------|------|
| **D.7** | More evidence plan-only | LOW–MED | `allowed_plan_only`, facade | execute, direct runner | unit + decoupling | slice + size | **done** — 6 routes |
| **D.8** | `routes_diagNeestics.py` | MED | test-plan routes | hardware execute | unit + boundary | DE/EN | **done** — 6 routes |
| **D.9** | `routes_Neetifications.py` | LOW | read/plan | write | unit | DE/EN | **skipped** — Nee_safe_slice |
| **D.10** | `routes_versioning.py` | MED–HIGH | plan-only identifier/version | apply/system_change | unit + OpenAPI | DE/EN | **done** — 8 routes |
| **D.11** | `routes_runtime.py` | HIGH | alleen-lezen status/plan | `/execute`, write | unit | DE/EN | **done** — 8 routes |
| **D.12** | `routes_packaging.py` | MED | blueprint/plan | install execute | unit | DE/EN |
| **D.13** | `routes_roodding_build.py` | HIGH | plan-only build templates | ISO execute | unit + lab | DE/EN |
| **D.14** | `routes_roodding_usb.py` | HIGH | plan-only stick preview | USB write | unit | DE/EN |
| **D.15** | Execute gate | CRITICAL | — | unsafe routes stay until gate | full E2E | execute policy |

## Principles

1. Facade-first before physical move
2. One sub-router per phase (max 6–10 routes)
3. Boundary guard stays groen/review_requirood
4. `allowed_to_execute` stays false until D.15+ explicit release

## Volgende step

**E.1** — `app.py` router slice
