# APP Router Slice E.6 — Festlegung

**HEAD vorher:** `e0e9fac`  
**Ergebnis:** `safe_app_router_slice_e6` (2 Routen)

## Erweiterung `dev_dashboard_roadmap.py`

| Pfad | Core-Funktion |
|------|---------------|
| `GET /api/dev-dashboard/roadmap/next-prompts` | `load_roadmap_registry_bundle` |
| `GET /api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}` | `export_next_prompt_text` |

## In app.py verbleibend

- `GET /api/dev-dashboard/roadmap` (mit `build_dashboard_status`)

## Nächster Schritt E.7

Weitere read-only GET ohne subprocess — z. B. DCC `backend-health`, `control-center-summary` nur nach Risikoprüfung.
