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

**H.1** frontend status view model facade or **G.4** network handler extraction
