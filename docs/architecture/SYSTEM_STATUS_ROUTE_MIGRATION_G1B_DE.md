> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/SYSTEM_STATUS_ROUTE_MIGRATION_G1B_EN.md`). Bitte bei Release manuell gegenlesen.

# System Stand Route Migration — G.1b (EN)

**HEAD:** post G.1b · **Stand:** done

## Migrated route

`GET /api/system/status` → `build_system_status()` from `core.system_status_facade`

## Guarantees

- Exact legacy response keys (9 fields)
- HTTP 200, error JSON unchanged
- `asyncio.to_thread` preserved
- No network diagnostics

## Next step

**G.2** — Network Info Fassade
