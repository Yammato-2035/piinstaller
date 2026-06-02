# app.py — Zustand vor Decomposition (Baseline)

**Stand:** 2026-06-02 (Inventar zu Auftragsbeginn)

## Kennzahlen

| Metrik | Wert |
|--------|------|
| Zeilen (`wc -l`) | ~17 742 |
| `include_router(` | massenhaft in `app.py` (inkl. optionale Dev/Fleet/Rescue) |
| `@app.middleware` | mehrere Decorator-Registrierungen |

## Enthaltene Blöcke (Klassifikation)

| Block | Zielmodul | In diesem Lauf | Risiko |
|-------|-----------|----------------:|--------|
| FastAPI-Instanz + Lifespan | `app_bootstrap.app_factory` | Ja | niedrig |
| Middleware (CORS, Profil-Gate, Logging) | `app_bootstrap.middleware_registry` | Ja | mittel |
| Optionale Router (dev-server, fleet, dev-diagnostics, rescue-remote, rescue-agent) | `app_bootstrap.router_registry` | Ja | mittel |
| Kern-/Legacy-Routen (backup, restore, partitions, deploy, …) | `app.py` (TODO `APP_DECOMPOSITION_REMAINING`) | Nein (bewusst) | hoch |
| `/api/version` + Router-Diagnose | `app_bootstrap.version_router_diagnostics` | Ja | niedrig |
| Dev-Dashboard-Statusaggregation | `core.dev_dashboard_status_service` | Ja (Adapter) | mittel |
| Storage/Mount/Safety | `core/*_facade.py` | Facades gehärtet, Logik nicht dupliziert | mittel |

## Bewusst verbleibend

- Tausende Zeilen fachlicher Endpoints und Hilfsfunktionen in `app.py` (API-Kompatibilität, kein Big-Bang-Move).
