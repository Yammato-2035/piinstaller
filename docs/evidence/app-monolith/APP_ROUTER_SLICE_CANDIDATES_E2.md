# APP Router Slice — Kandidaten E.2

**HEAD (Baseline):** `0be2ab0` (nach E.1)  
**Kriterien:** GET, read-only, keine Schreiboperation, kein subprocess/systemctl/sudo, keine Storage-/Safety-/Mount-Duplikate.

## Ausgewählte E.2-Routen

| Route | Funktion | Domain | Risiko | E.2 geeignet | Grund |
|-------|----------|--------|--------|--------------|-------|
| `GET /api/settings` | `get_settings` | frontend_support | low | **ja** | Liest APP_SETTINGS/CONFIG_STATE, Disk-Read nur |
| `GET /api/settings/notifications/email` | `get_notification_email_settings` | frontend_support | low | **ja** | `core.notification_settings.build_public_settings` |
| `GET /api/presets/list` | `api_list_presets` | frontend_support | low | **ja** | Presets-Modul, kein subprocess |
| `GET /api/debug/routes` | `debug_routes` | diagnostics | low | **ja** | Route-Liste via `request.app.routes` |
| `GET /api/user-profile` | `get_user_profile` | frontend_support | low | **ja** | Disk-Read user_profile.json, kein Write |

## Explizit ausgeschlossen

| Route | Funktion | Domain | Risiko | E.2 geeignet | Grund |
|-------|----------|--------|--------|--------------|-------|
| `GET /api/status` | `get_status` | health | medium | nein | `get_network_info()` nutzt subprocess |
| `GET /api/system/network` | `get_system_network` | runtime | medium | nein | subprocess via `get_network_info` |
| `GET /api/system/status` | `system_status` | runtime | medium | nein | `asyncio.to_thread`, apt/psutil |
| `GET /api/system/paths` | `get_system_paths` | runtime | medium | nein | `_root_mount_device()` |
| `GET /api/dev-dashboard/*` | diverse | dev_dashboard | high | nein | DCC-Aggregation |
| `GET /api/users/sudo-password/check` | `check_sudo_password` | security | medium | nein | sudo-Bezug |
| Backup/Restore/Deploy/Rescue | diverse | diverse | high | nein | Domänen-Ausschluss |
| POST/PUT/DELETE | diverse | diverse | high | nein | Schreiboperationen |

## Module-Reuse

- `core.notification_settings` — E-Mail-Settings GET
- `presets` — Preset-Liste (via app `_list_presets_impl`)
- `core.versioning` — Version in debug/routes (via `get_pi_installer_version`)
- Lazy-Imports aus `app` für CONFIG/APP_SETTINGS/UserProfile (kein Zirkularimport beim Modul-Load)
