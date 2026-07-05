> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/NETWORK_INFO_ROUTE_MIGRATION_G2B_EN.md`). Bitte bei Release manuell gegenlesen.

# Network Info Route Migration — G.2b (EN)

**HEAD:** post G.2b · **Stand:** done

## Migrated routes

| Route | Fassade function |
|-------|-----------------|
| `GET /api/status` | `build_network_info` / `build_demo_network_info` |
| `GET /api/system/network` | `build_system_network_response` |

## Principles

- No API/response change
- No route move (stays in `app.py`)
- Legacy `get_network_info` / `_demo_network` only behind facade adapters
- Port detection via `_legacy_detect_frontend_port` (no new logic)

## Next step

**G.3 done** — see [NETWORK_INFO_CORE_CLEANUP_G3_EN.md](NETWORK_INFO_CORE_CLEANUP_G3_EN.md). **G.4 done** — [NETWORK_HANDLER_EXTRACTION_G4_EN.md](NETWORK_HANDLER_EXTRACTION_G4_EN.md).
