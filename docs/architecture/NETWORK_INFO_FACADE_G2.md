# Network Info Facade — Phase G.2

**HEAD:** nach G.2 · **Status:** CANONICAL_MODULE (FACADE)

## Zweck

Kanonischer read-only Einstieg für Netzwerkdiagnostik — Vorbereitung für `GET /api/status` und `GET /api/system/network` (G.2b).

## Modul

`backend/core/network_info_facade.py` · `FACADE_VERSION = 1`

## Öffentliche API

| Funktion | Delegiert an |
|----------|--------------|
| `build_network_info()` | `app.get_network_info` |
| `build_demo_network_info()` | `app._demo_network` |
| `build_network_status_section()` | Section-Wrapper |
| `build_network_info_diagnostics()` | Metadaten |
| `normalize_legacy_network_info()` | Facade-Status |

## Statuswerte

`ok`, `warning`, `degraded`, `blocked`, `unavailable`, `unknown` (via `build_section_status`)

## Regeln

- Keine Netzwerk-Schreiboperationen
- Kein nmcli/ip link/netplan in Facade-Modul
- Keine neue Discovery-Logik

## Tests

`backend/tests/test_network_info_facade_v1.py` — 8 Tests

## Nächster Schritt

**G.2b** — Router-Migration `GET /api/status` + `GET /api/system/network`

Evidence: [NETWORK_INFO_AUDIT_G2.md](../evidence/app-monolith/NETWORK_INFO_AUDIT_G2.md)
