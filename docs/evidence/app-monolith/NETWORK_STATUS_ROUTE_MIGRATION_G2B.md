# Network Status Route Migration — G.2b

**HEAD:** nach G.2b · **Route:** `GET /api/status`

## Änderung

| Vorher | Nachher |
|--------|---------|
| `_demo_network()` / `get_network_info()` direkt | `build_demo_network_info()` / `build_network_info()` via `network_info_facade` |

## Response (unverändert)

```json
{
  "status": "healthy",
  "hostname": "<aus network>",
  "version": "1.0.0",
  "network": { "ips", "hostname", ... }
}
```

## Verhalten

- Demo-Modus (`X-Demo-Mode: 1`) → `build_demo_network_info()`
- Live → `build_network_info()` → Legacy `app.get_network_info`
- Fehler → HTTP 500 (unverändert)
- Keine Facade-Metadaten in Response
