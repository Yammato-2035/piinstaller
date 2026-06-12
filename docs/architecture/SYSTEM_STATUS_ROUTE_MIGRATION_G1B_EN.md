# System Status Route Migration — G.1b (EN)

**HEAD:** post G.1b · **Status:** done

## Migrated route

`GET /api/system/status` → `build_system_status()` from `core.system_status_facade`

## Guarantees

- Exact legacy response keys (9 fields)
- HTTP 200, error JSON unchanged
- `asyncio.to_thread` preserved
- No network diagnostics

## Next step

**G.2** — Network Info Facade
