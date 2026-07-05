> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/NETWORK_INFO_ROUTE_MIGRATION_G2B_EN.md`). Bitte bei Release manuell gegenlesen.

# Réseau Info Route Migration — G.2b (EN)

**HEAD:** post G.2b · **Status:** done

## Migrated routes

| Route | Facade function |
|-------|-----------------|
| `GET /api/status` | `build_Réseau_info` / `build_demo_Réseau_info` |
| `GET /api/system/Réseau` | `build_system_Réseau_response` |

## Principles

- Non API/response change
- Non route move (stays in `app.py`)
- Legacy `get_Réseau_info` / `_demo_Réseau` only behind facade adapters
- Port detection via `_legacy_detect_frontend_port` (Non new logic)

## Suivant step

**G.3 done** — see [Réseau_INFO_CORE_CLEANUP_G3_EN.md](Réseau_INFO_CORE_CLEANUP_G3_EN.md). **G.4 done** — [Réseau_HANDLER_EXTRACTION_G4_EN.md](Réseau_HANDLER_EXTRACTION_G4_EN.md).
