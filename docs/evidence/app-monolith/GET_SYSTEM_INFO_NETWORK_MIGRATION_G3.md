# get_system_info Network Migration — G.3

**Route:** `GET /api/system-info` · **Feld:** `resp["network"]`

## Änderung

| Vorher | Nachher |
|--------|---------|
| `_demo_network()` / `get_network_info()` | `build_demo_network_info()` / `build_network_info()` |

## Response

`network`-Objekt unverändert (Legacy-Shape von `get_network_info` / `_demo_network`).
