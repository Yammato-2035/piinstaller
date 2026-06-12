# KB: APP Router Slice E.4

DCC-Index-Routen gehören in `dev_dashboard_readonly.py` und rufen **nur** Core-Funktionen auf (`build_modules_list`, `build_evidence_index`, …).

Keine `os.walk`/`rglob` in Router-Dateien.

Details: [APP_ROUTER_SLICE_E4.md](../../architecture/APP_ROUTER_SLICE_E4.md)
