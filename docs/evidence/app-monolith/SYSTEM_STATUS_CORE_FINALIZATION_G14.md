# System Status Core Finalization G.14

**Kampagne:** A.4 · **Version:** 1.7.15.0

## Stack

```
system_status_facade
  → system_status_core (kein import app)
    → system_status_providers (app nur für Security/Updates)
```

## Entfernte app-Abhängigkeiten in core

| Vorher (`system_status_core`) | Nachher (`system_status_providers`) |
|-------------------------------|---------------------------------------|
| `import app` → `APP_SETTINGS.backup.realtest_state` | `load_backup_realtest_state()` aus `config.json` |
| `import app` → `get_security_config()` | `provide_security_config()` |
| `import app` → `get_updates_categorized()` | `provide_updates_categorized()` |

## Modul

`backend/core/system_status_providers.py` · `SYSTEM_STATUS_PROVIDER_VERSION = 1`

## Tests

`test_system_status_providers_v1` — core ohne `import app`
