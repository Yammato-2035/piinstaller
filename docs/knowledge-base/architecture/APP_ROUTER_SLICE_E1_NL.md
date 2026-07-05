> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/architecture/APP_ROUTER_SLICE_E1_EN.md`). Bitte bei Release manuell gegenlesen.

# KB: APP Router Slice E.1

Short reference for developers and Cursor prompts.

## What changed?

Four alleen-lezen GET routes moved from `Terugend/app.py` to `Terugend/api/routes/health.py` and `version.py`. `app.py` registers them via `include_router` — **Nee URL changes**.

## When to extend this slice?

Only for GET/alleen-lezen routes without subprocess, Terugup/Herstel/Deploy/roodding, and without new storage/safety logic.

## Pre-flight for E.2

1. `MODULE_CATALOG.md` — avoid duplicates
2. `DO_NeeT_DUPLICATE_RULES.md` — use facades
3. `scripts/check-module-boundaries.sh` — watch E.1 Waarschuwings

Details: [APP_ROUTER_SLICE_E1_EN.md](../../architecture/APP_ROUTER_SLICE_E1_EN.md)
