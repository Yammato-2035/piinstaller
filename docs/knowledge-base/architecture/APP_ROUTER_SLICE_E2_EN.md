# KB: APP Router Slice E.2

Four router modules under `backend/api/routes/`: `health`, `version` (E.1), `settings`, `status` (E.2).

## Rule

GET-only without subprocess — write handlers stay in `app.py` until a dedicated slice phase.

Details: [APP_ROUTER_SLICE_E2_EN.md](../../architecture/APP_ROUTER_SLICE_E2_EN.md)
