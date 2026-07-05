> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/NETWORK_INFO_CORE_CLEANUP_G3_EN.md`). Bitte bei Release manuell gegenlesen.

# Netwerk Info Core Cleanup — G.3 (EN)

**HEAD:** post G.3 · **Status:** done

## Migrated handlers

| Handler | Facade |
|---------|--------|
| `get_system_info` | `build_Netwerk_info` / `build_demo_Netwerk_info` |
| `webserver_status` | `build_Netwerk_info` |

## Legacy remains

- `app.get_Netwerk_info` — implementation
- `app._demo_Netwerk` — demo placeholder
- Facade `_legacy_*` adapters

## Volgende step

Volgende: further `app.py` router slices — see [Netwerk_HANDLER_EXTRACTION_G4_EN.md](Netwerk_HANDLER_EXTRACTION_G4_EN.md).
