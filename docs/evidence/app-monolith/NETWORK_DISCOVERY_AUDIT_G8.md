# Network Discovery Audit — G.8

**HEAD vorher:** `73faaef` · **Branch:** `main`

## Legacy-Funktionen (vor Migration)

| Funktion | Zeile | ~Zeilen | Verantwortung |
|----------|-------|---------|---------------|
| `get_network_info()` | 5856 | 85 | LAN-IP-Erkennung (`ip -4`, `hostname -I`), Hostname |
| `_demo_network()` | 3122 | 3 | Statische Demo-Daten |
| `_detect_frontend_port()` | 3942 | 16 | Frontend-Port via `ss` (5173/3001/3002) |
| `_is_reachable_lan_ip()` | 5842 | 14 | IP-Filter (nur in Discovery) |

## Inputs / Outputs

### `discover_network_info()`

| | |
|---|---|
| **Inputs** | Keine Parameter; liest System (`ip`, `hostname`) |
| **Output-Keys** | `ips`, `localhost`, `primary_ip`, `interfaces`, `warnings`, `source`, `hostname` |
| **Seiteneffekte** | Read-only Shell (`ip`, `hostname`); Debug-Logging via `debug.logger` |
| **Fehlerfall** | `{"ips": [], "hostname": "unknown"}` |

### `discover_demo_network()`

| | |
|---|---|
| **Inputs** | Keine |
| **Output** | `{"ips": ["192.168.1.100"], "hostname": "raspberrypi"}` |
| **Seiteneffekte** | Keine |

### `detect_frontend_port()`

| | |
|---|---|
| **Inputs** | Keine |
| **Output** | `int` (5173, 3001, 3002 oder Default 3001) |
| **Seiteneffekte** | Read-only `ss` via `_shell_run` |

## Aufrufer (vor G.8)

| Aufrufer | Zugriff |
|----------|---------|
| `network_info_facade._legacy_*` | lazy `import app` → **Zyklus** |
| `app.get_network_info` | Direktimplementierung |
| Tests | `test_network_and_monitoring_status_v1`, `test_debug_instrumentation` |

## Legacy-Abhängigkeiten (vor G.8)

```
network_info_facade → import app → get_network_info() → run_command/subprocess
```

## Nach G.8

```
network_info_facade → network_discovery.py (kein app-Import)
app.py → dünne Wrapper → network_discovery.py
```

## Facade-Kette (Ziel erreicht)

| Layer | Modul |
|-------|-------|
| HTTP | `webserver_status_facade` / `network` router |
| Network API | `network_info_facade` |
| Discovery | `network_discovery` |
