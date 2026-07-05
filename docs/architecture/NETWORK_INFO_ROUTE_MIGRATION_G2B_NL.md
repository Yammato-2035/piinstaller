> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/NETWORK_INFO_ROUTE_MIGRATION_G2B_EN.md`). Bitte bei Release manuell gegenlesen.

# Netwerk Info Route Migration — G.2b (EN)

**HEAD:** post G.2b · **Status:** done

## Migrated routes

| Route | Facade function |
|-------|-----------------|
| `GET /api/status` | `build_Netwerk_info` / `build_demo_Netwerk_info` |
| `GET /api/system/Netwerk` | `build_system_Netwerk_response` |

## Principles

- Nee API/response change
- Nee route move (stays in `app.py`)
- Legacy `get_Netwerk_info` / `_demo_Netwerk` only behind facade adapters
- Port detection via `_legacy_detect_frontend_port` (Nee new logic)

## Volgende step

**G.3 done** — see [Netwerk_INFO_CORE_CLEANUP_G3_EN.md](Netwerk_INFO_CORE_CLEANUP_G3_EN.md). **G.4 done** — [Netwerk_HANDLER_EXTRACTION_G4_EN.md](Netwerk_HANDLER_EXTRACTION_G4_EN.md).
