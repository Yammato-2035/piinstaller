# Network Info Core Cleanup — G.3 (EN)

**HEAD:** post G.3 · **Status:** done

## Migrated handlers

| Handler | Facade |
|---------|--------|
| `get_system_info` | `build_network_info` / `build_demo_network_info` |
| `webserver_status` | `build_network_info` |

## Legacy remains

- `app.get_network_info` — implementation
- `app._demo_network` — demo placeholder
- Facade `_legacy_*` adapters

## Next step

Next: further `app.py` router slices — see [NETWORK_HANDLER_EXTRACTION_G4_EN.md](NETWORK_HANDLER_EXTRACTION_G4_EN.md).
