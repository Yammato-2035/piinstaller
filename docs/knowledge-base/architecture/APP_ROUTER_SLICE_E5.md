# KB: APP Router Slice E.5

Roadmap-Subroutes gehören in `dev_dashboard_roadmap.py` und rufen **nur** `load_roadmap_registry_bundle` auf.

`GET /api/dev-dashboard/roadmap` (volles Bundle mit Dashboard-Context) bleibt vorerst in `app.py`.

Details: [APP_ROUTER_SLICE_E5.md](../../architecture/APP_ROUTER_SLICE_E5.md)
