# Network Direct Usage — G.3

**HEAD:** nach G.3

| Datei | Funktion | Zugriff | Bewertung |
|-------|----------|---------|-----------|
| `app.py` | `get_status` | `build_network_info` | migrated_to_facade |
| `app.py` | `get_system_network` | `build_system_network_response` | migrated_to_facade |
| `app.py` | `get_system_info` | `build_network_info` / `build_demo_network_info` | migrated_to_facade |
| `app.py` | `webserver_status` | `build_network_info` | migrated_to_facade |
| `app.py` | `get_network_info` | subprocess/ip | legacy_adapter |
| `app.py` | `_demo_network` | statisch | legacy_adapter |
| `network_info_facade.py` | `_legacy_*` | `app.*` | allowed_facade |
| `tests/test_network_and_monitoring_status_v1.py` | Tests | `app.get_network_info` | allowed_facade |

**Keine `legacy_pending` Handler in app.py.**
