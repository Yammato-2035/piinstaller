# System Status Core Audit — G.12

**Datum:** 2026-06-10  
**HEAD (Start):** 23462c1

## Ist-Analyse

| Symbol | Ort | Rolle |
|--------|-----|-------|
| `_legacy_compute_ampel_status` | `system_status_facade` | → `app._compute_system_status` |
| `_compute_system_status` | `app.py` | Backup/Restore/Security/Updates Ampel |
| `get_security_config` | `app.py` | Security-Ampel (Adapter bleibt im Core) |
| `get_updates_categorized` | `app.py` | Updates-Ampel (Adapter bleibt im Core) |
| `APP_SETTINGS.backup.realtest_state` | `app.py` | Backup/Restore-Ampel |

## Ziel-Owner

`backend/core/system_status_core.py` — `SYSTEM_STATUS_CORE_VERSION = 1`

## Öffentliche API

- `build_backup_status()`, `build_restore_status()`, `build_security_status()`, `build_update_status()`
- `build_overall_status()`, `load_backup_realtest_state()`, `build_system_status_diagnostics()`

## Migration

- Facade: Ampel nur über `system_status_core.build_overall_status`
- `app._compute_system_status`: Wrapper → Core
- **Nicht migriert (bewusst):** `build_backend_runtime_section`, `build_installation_section`, `build_profile_section` (noch `import app` — G.13)

## Risiken

- `system_status_core` enthält kontrollierte `import app`-Adapter für Security/Updates (Zyklus nur Facade→app gebrochen)

## Tests

`test_system_status_core_v1`, `test_system_status_route_migration_g1b`
