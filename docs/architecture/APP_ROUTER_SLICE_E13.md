# App Router Slice E.13

**Phase:** Monolith-Auflösung — System POST utilities  
**Version:** 1.8.11.0

## Scope

| Route | Handler |
|-------|---------|
| `POST /api/system/run-update-in-terminal` | `run_update_in_terminal` |
| `POST /api/system/run-mixer` | `run_mixer` |
| `POST /api/system/install-mixer-packages` | `install_mixer_packages` |

Nach E.13 enthält `app.py` **keine** `@app.post("/api/system/…")` mehr.

## Security

- `run-update-in-terminal`: kein automatisches apt (nur `manual_required`)
- `run-mixer`: Allowlist `ALLOWED_MIXER_APPS`
- `install-mixer-packages`: sudo_store nur mit `has_password()`-Guard

## Tests

`test_app_router_slice_e13.py` — 20 Routen im System-Router.
