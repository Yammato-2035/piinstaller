# System Status Direct Usage — G.1b

| Datei | Funktion | Direktzugriff | Bewertung | Empfehlung |
|-------|----------|---------------|-----------|------------|
| `app.py` | `system_status` handler | `build_system_status` | **migrated_to_facade** | erledigt |
| `app.py` | `_compute_system_status` | Definition | **legacy_pending** | bleibt bis Core-Extraktion |
| `core/system_status_facade.py` | `build_system_status` | Facade-Owner | **allowed_facade** | kanonisch |
| `core/system_status_facade.py` | `_legacy_compute_ampel_status` | `app._compute_system_status` | **allowed_facade** | Legacy-Adapter |
| `tests/test_network_and_monitoring_status_v1.py` | Tests | `_compute_system_status` | **legacy_pending** | OK für Unit-Tests |
| `app.py` | `get_status` | `get_network_info` | **legacy_pending** | G.2 |

## HTTP `/api/system/status`

**Kein** direkter `_compute_system_status` / `APP_SETTINGS`-Zugriff mehr im Handler.
