# System Status Audit — Phase G.1

**HEAD:** `ec67a7b` · **Scope:** statische Analyse

## GET /api/status (app.py)

| Feld | Quelle | Netzwerk? |
|------|--------|-----------|
| `status` | Konstante `"healthy"` | nein |
| `hostname` | `get_network_info()` / `_demo_network()` | **ja → G.2** |
| `version` | Hardcoded `"1.0.0"` | nein |
| `network` | `get_network_info()` / Demo | **ja → G.2** |

## GET /api/system/status (app.py)

| Feld | Quelle | Ampel? |
|------|--------|--------|
| `backup/restore/security/updates` | `_compute_system_status()` | ja |
| `realtest_state` | `APP_SETTINGS.backup` | nein |
| Wrapper | `status`, `api_status`, `data` | nein |

## Pflichttabelle

| Quelle | Funktion | Status-Felder | Direktzugriffe | Seiteneffekt | Empfehlung |
|--------|----------|---------------|----------------|--------------|------------|
| `app.py` | `get_status` | healthy, hostname, version, network | `get_network_info`, subprocess | read-only | G.2 Network Facade für network/hostname |
| `app.py` | `system_status` | ampel + realtest_state | `_compute_system_status` | read-only | G.1b → `build_system_status` |
| `app.py` | `_compute_system_status` | backup/restore/security/updates | `APP_SETTINGS`, `get_security_config`, `get_updates_categorized` | subprocess via delegates | Legacy-Adapter in Facade |
| `app.py` | `get_security_config` | security ampel inputs | `run_command`, UFW/SSH | subprocess/sudo | bleibt in app bis Core-Extraktion |
| `app.py` | `get_updates_categorized` | updates ampel | `apt list` via run_command | subprocess | bleibt in app |
| `core/install_paths` | `get_backend_runtime_dir` | runtime_path | none | none | Facade `build_backend_runtime_section` |
| `api/routes/status.py` | `self_update_status` | installation drift | app version helpers | read files | Facade `build_installation_section` |
| `api/routes/status.py` | `get_user_profile` | profile | `_user_profile_collect_from_disk` | read files | Facade `build_profile_section` |
| `api/routes/health.py` | `health_check` | liveness | `build_health_payload` | none | separater Health-Track |

## Bewertung G.1

- **Facade-Scope:** Ampel (`/api/system/status`), Backend-Runtime, Installation, Profil
- **Ausgeschlossen G.1:** Netzwerk (`/api/status` network block) → G.2
- **Keine Route-Migration in G.1**
