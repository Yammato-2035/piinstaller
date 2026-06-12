# System Status Facade — Phase G.1

**HEAD:** nach G.1 · **Status:** CANONICAL_MODULE (FACADE)

## Zweck

Kanonischer read-only Einstieg für Systemstatus — Vorbereitung für `GET /api/status` und `GET /api/system/status` Router-Migration (G.1b), **ohne** API- oder Route-Änderung in G.1.

## Modul

`backend/core/system_status_facade.py` · `FACADE_VERSION = 1`

## Öffentliche API

| Funktion | Delegiert an |
|----------|--------------|
| `build_system_status()` | Sections + Legacy-Ampel-Adapter |
| `build_system_status_sections()` | alle Sections |
| `build_backend_runtime_section()` | `install_paths`, `app.get_pi_installer_version` |
| `build_installation_section()` | app version/opt drift |
| `build_profile_section()` | `app._user_profile_collect_from_disk` |
| `build_system_status_diagnostics()` | Metadaten |

## Statuswerte

`ok`, `warning`, `degraded`, `blocked`, `unavailable`, `unknown`

Legacy-Ampel `green/yellow/red` via `normalize_legacy_system_status`.

## Regeln

- Kein subprocess, systemctl, sudo in Facade-Modul
- Keine Netzwerkdiagnostik (G.2)
- `build_section_status` aus `dcc_status_facade` (koordinierte Taxonomie)
- Section-Fehler isoliert (`unavailable`)

## Tests

`backend/tests/test_system_status_facade_v1.py` — 9 Tests

## Nächster Schritt

**G.1b** — abgeschlossen. **G.2** — Network Info Facade.

Evidence: [SYSTEM_STATUS_ROUTE_MIGRATION_G1B.md](SYSTEM_STATUS_ROUTE_MIGRATION_G1B.md)
