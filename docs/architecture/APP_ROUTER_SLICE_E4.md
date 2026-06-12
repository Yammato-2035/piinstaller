# APP Router Slice E.4

**Baseline HEAD:** `c36c304` · **Status:** erledigt

## Extrahierte Routen (5)

Neues Modul `api/routes/dev_dashboard_readonly.py` — delegiert ausschließlich an `core.dev_dashboard*` und verwandte Core-Indexer. **Keine** neuen Dateiscanner in der Router-Datei.

## Metriken

`app.py`: 17.617 → 17.568 Zeilen; 199 → 194 Routen.

## Nächster Schritt

**E.5** — Roadmap read-only Subroutes (`load_roadmap_registry_bundle`).
