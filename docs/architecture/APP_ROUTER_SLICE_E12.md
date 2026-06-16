# App Router Slice E.12

**Phase:** Monolith-Auflösung — System status + hardware probes  
**Version:** 1.8.10.0

## Scope

| Route | Handler |
|-------|---------|
| `GET /api/system/status` | `system_status` |
| `GET /api/system/freenove-detection` | `get_freenove_detection` |
| `GET /api/system/asus-rog/fan/profiles` | `get_asus_fan_profiles` |
| `GET /api/system/asus-rog/fan/status` | `get_asus_fan_status` |
| `POST /api/system/asus-rog/fan/set-profile` | `set_asus_fan_profile` |
| `GET /api/system/asus-rog/detection` | `get_asus_rog_detection` |

## Bugfix

`detect_freenove_case` war in `app.py` referenziert aber nicht definiert — implementiert in `core/hardware_discovery.py`.

## Security

`set_asus_fan_profile` speichert Sudo-Passwort nur bei `sudo_store.has_password() == false`.

## Tests

- `test_app_router_slice_e12.py` — 17 Routen im System-Router
- `test_security_sudo_store_has_password_guard_v1.py`
