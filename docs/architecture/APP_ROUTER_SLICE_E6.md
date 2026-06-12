# APP Router Slice E.6

**Baseline HEAD:** `e0e9fac` · **Status:** erledigt

## Extrahierte Routen (2)

Erweiterung von `api/routes/dev_dashboard_roadmap.py`:

- `GET /api/dev-dashboard/roadmap/next-prompts`
- `GET /api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}`

Nur `core.dev_dashboard_roadmap` — kein `build_dashboard_status`.

## Metriken

`app.py`: 17.499 → 17.472 Zeilen; 189 → 187 Routen.

## Nächster Schritt

**E.7** — weiterer read-only Slice (ohne DCC-Aggregation).
