> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/APP_ROUTER_SLICE_E3_EN.md`). Bitte bei Release manuell gegenlesen.

# APP Router Slice E.3

**Baseline HEAD:** `b667785` · **Stand:** done

## Extracted routes (5)

| Path | Module |
|------|--------|
| `GET /api/logs/tail` | `health.py` |
| `GET /api/self-update/status` | `status.py` |
| `GET /api/apps` | `catalog.py` |
| `GET /api/dev-dashboard/capability-status` | `capabilities.py` |
| `GET /api/dev-dashboard/compact-status` | `capabilities.py` |

## Metrics

`app.py`: 17,699 → 17,617 lines; 204 → 199 routes.

## Next step

**E.4** — more file-based read-only GET routes.
