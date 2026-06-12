# Network Info Route Migration — G.2b (EN)

**HEAD:** post G.2b · **Status:** done

## Migrated routes

| Route | Facade function |
|-------|-----------------|
| `GET /api/status` | `build_network_info` / `build_demo_network_info` |
| `GET /api/system/network` | `build_system_network_response` |

## Principles

- No API/response change
- No route move (stays in `app.py`)
- Legacy `get_network_info` / `_demo_network` only behind facade adapters
- Port detection via `_legacy_detect_frontend_port` (no new logic)

## Next step

**G.3 done** — see [NETWORK_INFO_CORE_CLEANUP_G3_EN.md](NETWORK_INFO_CORE_CLEANUP_G3_EN.md). **H.1** or **G.4** next.
