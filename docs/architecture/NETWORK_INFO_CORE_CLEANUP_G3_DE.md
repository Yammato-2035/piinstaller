> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/NETWORK_INFO_CORE_CLEANUP_G3_EN.md`). Bitte bei Release manuell gegenlesen.

# Network Info Core Cleanup — G.3 (EN)

**HEAD:** post G.3 · **Stand:** done

## Migrated handlers

| Handler | Fassade |
|---------|--------|
| `get_system_info` | `build_network_info` / `build_demo_network_info` |
| `webserver_status` | `build_network_info` |

## Legacy remains

- `app.get_network_info` — implementation
- `app._demo_network` — demo placeholder
- Fassade `_legacy_*` adapters

## Next step

Next: further `app.py` router slices — see [NETWORK_HANDLER_EXTRACTION_G4_EN.md](NETWORK_HANDLER_EXTRACTION_G4_EN.md).
