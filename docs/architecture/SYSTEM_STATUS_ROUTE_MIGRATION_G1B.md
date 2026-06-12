# System Status Route Migration — G.1b

**HEAD:** nach G.1b · **Status:** erledigt

## Migrierte Route

`GET /api/system/status` → `build_system_status()` aus `core.system_status_facade`

## Garantien

- Exakte Legacy-Response-Keys (9 Felder)
- HTTP 200, Fehler-JSON unverändert
- `asyncio.to_thread` beibehalten (Event-Loop-Schutz)
- Keine Netzwerkdiagnostik

## Nächster Schritt

**G.2** — Network Info Facade (`GET /api/status`, `GET /api/system/network`)
