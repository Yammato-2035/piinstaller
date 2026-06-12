# Network Info Audit — Phase G.2

**HEAD:** `6b27d87` · **Scope:** statische Analyse

## Pflichttabelle

| Quelle | Funktion | Netzwerk-Felder | Low-Level-Zugriffe | Seiteneffekt | Empfehlung |
|--------|----------|-----------------|-------------------|--------------|------------|
| `app.py` | `get_network_info` | ips, hostname, interfaces, warnings, source | `ip -4`, `subprocess hostname` | read-only | Facade `_legacy_get_network_info` |
| `app.py` | `_demo_network` | ips, hostname | keine | read-only | Facade `build_demo_network_info` |
| `app.py` | `get_status` | network-Block + hostname | delegiert | read-only | G.2b Facade |
| `app.py` | `get_system_network` | erweitert + ports | delegiert + `_detect_frontend_port` | read-only | G.2b Facade |
| `app.py` | `_is_demo_mode` | Header-Check | keine | read-only | Route-Layer G.2b |
| `tests/test_network_and_monitoring_status_v1.py` | Tests | diverse | mock subprocess | Test | beibehalten |

## GET /api/status

```json
{ "status": "healthy", "hostname", "version": "1.0.0", "network": { ... get_network_info shape } }
```

## GET /api/system/network

Zusätzlich: `status`, `frontend_port`, `backend_port`; Demo-Modus expandiert `_demo_network`.

## Bewertung G.2

- **Facade-Scope:** Delegation an Legacy, Normalisierung, Section-Contract
- **Keine Router-Migration in G.2**
- **Rettungsstick/Diagnose:** `source`, `warnings`, `interfaces` relevant für read-only Evidence
