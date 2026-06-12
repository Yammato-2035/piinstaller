# Network Core Cleanup — G.3

**HEAD:** nach G.3 · **Scope:** verbleibende `app.py`-Handler

## Pflichttabelle

| Datei | Funktion | Direkter Netzwerkzugriff | Ziel | Migration geeignet | Grund |
|-------|----------|--------------------------|------|-------------------|-------|
| `app.py` | `get_system_info` | `_demo_network` / `get_network_info` | Facade | ja | read-only, gleicher Shape |
| `app.py` | `webserver_status` | `get_network_info` | Facade | ja | read-only, gleicher Shape |
| `app.py` | `get_network_info` | subprocess/ip | Legacy-Impl. | nein | Facade-Adapter-Ziel |
| `app.py` | `_demo_network` | statisch | Legacy-Impl. | nein | Facade-Adapter-Ziel |
| `network_info_facade.py` | `_legacy_*` | `app.*` | Adapter | nein | kanonisch |

## Ergebnis G.3

Alle Handler-Direktzugriffe in `app.py` entfernt. Legacy-Implementierung bleibt für Facade-Delegation.
