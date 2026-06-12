# KB: APP Router Slice E.1

Short reference for developers and Cursor prompts.

## What changed?

Four read-only GET routes moved from `backend/app.py` to `backend/api/routes/health.py` and `version.py`. `app.py` registers them via `include_router` — **no URL changes**.

## When to extend this slice?

Only for GET/read-only routes without subprocess, backup/restore/deploy/rescue, and without new storage/safety logic.

## Pre-flight for E.2

1. `MODULE_CATALOG.md` — avoid duplicates
2. `DO_NOT_DUPLICATE_RULES.md` — use facades
3. `scripts/check-module-boundaries.sh` — watch E.1 warnings

Details: [APP_ROUTER_SLICE_E1_EN.md](../../architecture/APP_ROUTER_SLICE_E1_EN.md)
