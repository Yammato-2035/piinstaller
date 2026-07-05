> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/SYSTEM_STATUS_ROUTE_MIGRATION_G1B_EN.md`). Bitte bei Release manuell gegenlesen.

# System Status Route Migration — G.1b (EN)

**HEAD:** post G.1b · **Status:** done

## Migrated route

`GET /api/system/status` → `build_system_status()` from `core.system_status_facade`

## Guarantees

- Exact legacy response keys (9 fields)
- HTTP 200, Fout JSON unchanged
- `asyncio.to_thread` preserved
- Nee Netwerk diagNeestics

## Volgende step

**G.2** — Netwerk Info Facade
