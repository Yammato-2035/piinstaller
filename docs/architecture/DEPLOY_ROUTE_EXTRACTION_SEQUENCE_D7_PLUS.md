# Deploy Route Extraction Sequence D.7+

**Nach D.6 Orchestrator-Target** — kontrollierte Fortsetzung

| Phase | Ziel | Risiko | Erlaubt | Verboten | Tests | Doku |
|-------|------|--------|---------|----------|-------|------|
| **D.7** | Weitere Evidence plan-only | LOW–MED | `allowed_plan_only`, Facade | Execute, direct runner | Unit + decoupling | Slice + size | **erledigt** — 6 Routen |
| **D.8** | `routes_diagnostics.py` | MED | test-plan GET/POST plan | hardware execute | Unit + boundary | DE/EN | **erledigt** — 6 Routen |
| **D.9** | `routes_notifications.py` | LOW | read/plan (falls Routen existieren) | write | Unit | DE/EN | **übersprungen** — no_safe_slice |
| **D.10** | `routes_versioning.py` | MED–HIGH | plan-only identifier/version | apply/system_change | Unit + OpenAPI | DE/EN | **erledigt** — 8 Routen |
| **D.11** | `routes_runtime.py` | HIGH | read-only status/plan | `/execute`, write | Unit + E2E später | DE/EN |
| **D.12** | `routes_packaging.py` | MED | blueprint/plan | install execute | Unit | DE/EN |
| **D.13** | `routes_rescue_build.py` | HIGH | plan-only build templates | ISO execute | Unit + lab | DE/EN |
| **D.14** | `routes_rescue_usb.py` | HIGH | plan-only stick preview | USB write | Unit + operator | DE/EN |
| **D.15** | Execute-Gate | CRITICAL | — | unsafe routes **bleiben** bis Gate | Full E2E | Execute policy |

## Prinzipien

1. Facade-first (`build_plan_only_response`) vor physischem Move
2. Ein Subrouter pro Phase (max. 6–10 Routen)
3. Boundary-Guard muss grün/review_required bleiben
4. `allowed_to_execute` bleibt false bis D.15+ explizit freigegeben

## Nächster Schritt

**D.11** — `routes_runtime.py`
