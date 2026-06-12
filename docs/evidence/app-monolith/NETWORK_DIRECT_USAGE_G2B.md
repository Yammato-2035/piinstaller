# Network Direct Usage — G.2b

**HEAD:** nach G.2b

| Datei | Funktion | Direktzugriff | Bewertung | Empfehlung |
|-------|----------|---------------|-----------|------------|
| `backend/app.py` | `get_status` | `build_network_info` / `build_demo_network_info` | migrated_to_facade | erledigt G.2b |
| `backend/app.py` | `get_system_network` | `build_system_network_response` | migrated_to_facade | erledigt G.2b |
| `backend/app.py` | `get_network_info` | subprocess/ip/hostname | legacy_adapter | bleibt Legacy-Implementierung |
| `backend/app.py` | `_demo_network` | statische Demo-Daten | legacy_adapter | bleibt Legacy-Implementierung |
| `backend/app.py` | `get_system_info` | `get_network_info` / `_demo_network` | legacy_pending | G.3 Facade |
| `backend/app.py` | `webserver_status` | `get_network_info` | legacy_pending | G.3 Facade |
| `backend/core/network_info_facade.py` | `_legacy_*` | `app.get_network_info` etc. | allowed_facade | kanonischer Adapter |
| `backend/tests/test_network_and_monitoring_status_v1.py` | diverse | `app.get_network_info` | allowed_facade | Legacy-Unit-Tests |
| `backend/tests/test_debug_instrumentation.py` | debug | `get_network_info` | allowed_facade | Instrumentation |
