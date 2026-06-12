# KB: APP Router Slice E.2

Vier Router-Module unter `backend/api/routes/`: `health`, `version` (E.1), `settings`, `status` (E.2).

## Regel

Nur GET ohne subprocess — Schreib-Handler bleiben in `app.py` bis eigene Slice-Phase.

Details: [APP_ROUTER_SLICE_E2.md](../../architecture/APP_ROUTER_SLICE_E2.md)
