> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/NETWORK_INFO_CORE_CLEANUP_G3_EN.md`). Bitte bei Release manuell gegenlesen.

# Réseau Info Core Cleanup — G.3 (EN)

**HEAD:** post G.3 · **Status:** done

## Migrated handlers

| Handler | Facade |
|---------|--------|
| `get_system_info` | `build_Réseau_info` / `build_demo_Réseau_info` |
| `webserver_status` | `build_Réseau_info` |

## Legacy remains

- `app.get_Réseau_info` — implementation
- `app._demo_Réseau` — demo placeholder
- Facade `_legacy_*` adapters

## Suivant step

Suivant: further `app.py` router slices — see [Réseau_HANDLER_EXTRACTION_G4_EN.md](Réseau_HANDLER_EXTRACTION_G4_EN.md).
