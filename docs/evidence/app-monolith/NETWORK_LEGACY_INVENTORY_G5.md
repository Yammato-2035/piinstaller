# Network Legacy Inventory — G.5

**HEAD:** `307c411`

## Legacy-Funktionen in `app.py`

| Funktion | Zeile | ~Zeilen | Technik | Klassifikation |
|----------|-------|---------|---------|----------------|
| `_demo_network()` | 3122 | 3 | Statische Demo-Daten | **LEGACY_ADAPTER** |
| `_detect_frontend_port()` | 3942 | 16 | `run_command` + `ss -tuln` | **LEGACY_ADAPTER** |
| `get_network_info()` | 5856 | 85 | `ip -4`, `hostname -I`, `subprocess hostname` | **LEGACY_ADAPTER** |

## Direkte Nutzer

### `get_network_info()`

| Nutzer | Klassifikation |
|--------|----------------|
| `network_info_facade._legacy_get_network_info` | **CANONICAL** (einziger produktiver Pfad) |
| `test_network_and_monitoring_status_v1.py` | erlaubt (Legacy-Shape-Test) |
| `test_debug_instrumentation.py` | erlaubt (Instrumentation) |

Kein HTTP-Handler ruft `get_network_info()` mehr direkt auf (G.3 erledigt).

### `_demo_network()`

| Nutzer | Klassifikation |
|--------|----------------|
| `network_info_facade._legacy_demo_network` | **CANONICAL** |
| `_is_demo_mode(request)` indirekt via Facade | **CANONICAL** |

Kein direkter Handler-Aufruf mehr in `app.py`.

### `_detect_frontend_port()`

| Nutzer | Klassifikation |
|--------|----------------|
| `network_info_facade._legacy_detect_frontend_port` | **CANONICAL** |
| `webserver_status` (Z.8520) | **BLOCKED** — direkter Aufruf, nicht über Facade |
| `build_system_network_response` (via Facade) | **CANONICAL** |

## Migrationskandidaten (Implementierung aus `app.py` heraus)

| Symbol | Ziel (vorgeschlagen) | Klassifikation | Priorität |
|--------|----------------------|----------------|-----------|
| `get_network_info` | `core/network_discovery.py` oder Facade-Body | **MIGRATION_CANDIDATE** | CRITICAL |
| `_demo_network` | Facade-intern / `core/network_demo.py` | **MIGRATION_CANDIDATE** | LOW |
| `_detect_frontend_port` | `core/frontend_runtime_facade.py` oder Port-Modul | **MIGRATION_CANDIDATE** | MEDIUM |

## Verwandte Helfer (nicht Network-Owner, aber Kopplung)

| Funktion | Zeile | Nutzer u. a. | Klassifikation |
|----------|-------|--------------|----------------|
| `_is_demo_mode` | 3117 | network router, `get_system_info` | **CANONICAL** (HTTP-Concern, bleibt app) |
| `_is_reachable_lan_ip` | ~5840 | `get_network_info` | **MIGRATION_CANDIDATE** (mit Discovery) |
| `run_command` | global | Discovery, webserver, systeminfo | **BLOCKED** (shared app helper) |

## Zusammenfassung

| Klasse | Anzahl Symbole |
|--------|----------------|
| CANONICAL (Facade-Pfad) | 3 Adapter + 2 Router-Handler |
| LEGACY_ADAPTER (Implementierung in app.py) | 3 |
| MIGRATION_CANDIDATE | 4 (+ `_is_reachable_lan_ip`) |
| BLOCKED (direkter Bypass / Monolith-Handler) | 2 (`webserver_status` port + Handler) |
| OUT_OF_SCOPE | 1 (`dsi_radio`) |

**Keine `legacy_pending` HTTP-Handler** für `get_network_info` / `_demo_network` — G.3/G.4 erledigt.
