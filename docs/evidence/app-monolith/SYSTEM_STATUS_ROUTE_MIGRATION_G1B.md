# System Status Route Migration — G.1b

**Route:** `GET /api/system/status`  
**HEAD:** `9a897d1` → G.1b

## Änderung

| Vorher | Nachher |
|--------|---------|
| `asyncio.to_thread(_compute_system_status)` + `APP_SETTINGS` | `asyncio.to_thread(build_system_status)` |
| Direkt in Handler | `core.system_status_facade` |

## Response (unverändert)

```json
{
  "status": "success",
  "api_status": "ok",
  "message": "",
  "data": { "backup", "restore", "security", "updates", "realtest_state" },
  "backup", "restore", "security", "updates",
  "realtest_state"
}
```

Keine zusätzlichen Facade-Envelope-Keys in der HTTP-Response.

## Nicht migriert

- `GET /api/status` (network → G.2)
- `GET /api/system/network` (G.2)
