# Roadmap Subrouter Boundary — Phase F.3

**Modul:** `backend/api/routes/dev_dashboard_roadmap.py`  
**HEAD:** `8bb910c`

## Routen

| Route | `load_roadmap_registry_bundle` | `dashboard_context` | Facade |
|-------|-------------------------------|---------------------|--------|
| `GET .../roadmap/areas` | ja (ohne args) | nein | umgeht Facade |
| `GET .../milestones` | ja | nein | umgeht Facade |
| `GET .../blockers` | ja | nein | umgeht Facade |
| `GET .../decisions` | ja | nein | umgeht Facade |
| `GET .../next-prompt` | ja | nein | umgeht Facade |
| `GET .../next-prompts` | ja | nein | umgeht Facade |
| `GET .../export-next-prompt/{id}` | nein (`export_next_prompt_text`) | nein | OK |

## Root vs. Subroutes

| Endpoint | Owner | `dashboard_context` |
|----------|-------|---------------------|
| `GET /api/dev-dashboard/roadmap` (app.py) | `build_dcc_roadmap_api_bundle` | **ja** (F.2) |
| Subroutes `/roadmap/*` | `load_roadmap_registry_bundle()` direkt | **nein** |

## Bewertung

**Ergebnis: `boundary_ok_registry_only`**

- Subroutes liefern **reine Registry-Slices** (areas, milestones, …) ohne Runtime-Overlay.
- `load_roadmap_registry_bundle()` ohne `dashboard_context` ist **erlaubt** — kein `build_dashboard_status`.
- Boundary-Guard `dcc_status_router_bypasses_facade` ist **informativ**, kein Blocker.

## Künftig Facade?

| Szenario | Empfehlung |
|----------|------------|
| Registry-Slices unverändert | **beibehalten** — direkter Core-Call OK |
| Runtime-Overlay in Subroutes | `build_dcc_roadmap_api_bundle` oder Facade-Section |
| Einheitlicher Response-Wrapper | optional `build_dcc_roadmap_registry_slice()` in Facade (F.4, low priority) |

**Kein `needs_split` / `unsafe`** für aktuellen Stand.
