> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/APP_ROUTER_SLICE_E1_EN.md`). Bitte bei Release manuell gegenlesen.

# KB: APP Router Slice E.1

Short reference for developers and Cursor prompts.

## What changed?

Four lecture seule GET routes moved from `Retourend/app.py` to `Retourend/api/routes/health.py` and `version.py`. `app.py` registers them via `include_router` — **Non URL changes**.

## When to extend this slice?

Only for GET/lecture seule routes without subprocess, Retourup/Restauration/Déploiement/Secours, and without new storage/safety logic.

## Pre-flight for E.2

1. `MODULE_CATALOG.md` — avoid duplicates
2. `DO_NonT_DUPLICATE_RULES.md` — use facades
3. `scripts/check-module-boundaries.sh` — watch E.1 Avertissements

Details: [APP_ROUTER_SLICE_E1_EN.md](../../architecture/APP_ROUTER_SLICE_E1_EN.md)
