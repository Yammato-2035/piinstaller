# Deploy Route Extraction Sequence D.7+

**After D.6 orchestrator target** — controlled continuation

| Phase | Goal | Risk | Allowed | Forbidden | Tests | Docs |
|-------|------|------|---------|-----------|-------|------|
| **D.7** | More evidence plan-only | LOW–MED | `allowed_plan_only`, facade | execute, direct runner | unit + decoupling | slice + size |
| **D.8** | `routes_diagnostics.py` | MED | test-plan routes | hardware execute | unit + boundary | DE/EN |
| **D.9** | `routes_notifications.py` | LOW | read/plan | write | unit | DE/EN |
| **D.10** | `routes_versioning.py` | MED–HIGH | plan-only identifier/version | apply/system_change | unit | DE/EN |
| **D.11** | `routes_runtime.py` | HIGH | read-only status/plan | `/execute`, write | unit | DE/EN |
| **D.12** | `routes_packaging.py` | MED | blueprint/plan | install execute | unit | DE/EN |
| **D.13** | `routes_rescue_build.py` | HIGH | plan-only build templates | ISO execute | unit + lab | DE/EN |
| **D.14** | `routes_rescue_usb.py` | HIGH | plan-only stick preview | USB write | unit | DE/EN |
| **D.15** | Execute gate | CRITICAL | — | unsafe routes stay until gate | full E2E | execute policy |

## Principles

1. Facade-first before physical move
2. One sub-router per phase (max 6–10 routes)
3. Boundary guard stays green/review_required
4. `allowed_to_execute` stays false until D.15+ explicit release

## Next step

**D.7** — additional evidence routes with clear facade mapping
