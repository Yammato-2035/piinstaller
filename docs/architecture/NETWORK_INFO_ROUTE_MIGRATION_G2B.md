# Network Info Route Migration — G.2b

**HEAD:** nach G.2b · **Status:** erledigt

## Migrierte Routen

| Route | Facade-Funktion |
|-------|-----------------|
| `GET /api/status` | `build_network_info` / `build_demo_network_info` |
| `GET /api/system/network` | `build_system_network_response` |

## Prinzipien

- Keine API-/Response-Änderung
- Keine Route-Verschiebung (bleibt in `app.py`)
- Legacy `get_network_info` / `_demo_network` nur hinter Facade-Adapter
- Port-Erkennung über `_legacy_detect_frontend_port` (keine neue Logik)

## Tests

`backend/tests/test_network_info_route_migration_g2b.py`

## Nächster Schritt

**G.3** — verbleibende Direktzugriffe (`get_system_info`, `webserver_status`) oder **H.1** Frontend Status ViewModel
