# Backup Execute Router B.6

**Phase:** Monolith-Auflösung — Backup POST-Slice 6  
**Version:** 1.8.8.0

## Scope

Vier POST-Routen aus `app.py` nach `backup_execute.py` / `backup_execute_handlers.py`:

| Route | Handler |
|-------|---------|
| `POST /api/backup/target-prepare` | `backup_target_prepare` |
| `POST /api/backup/usb/mount` | `backup_usb_mount` |
| `POST /api/backup/usb/prepare` | `backup_usb_prepare` |
| `POST /api/backup/usb/eject` | `backup_usb_eject` |

`POST /api/backup/clone` bleibt in `app.py` (nächster Slice B.7).

## Runtime

Neue Adapter in `backup_readonly_runtime.py`:

- `mountpoints_for_disk`
- `sanitize_label`

## Tests

`backend/tests/test_backup_execute_router_b6_v1.py` — 13 POST-Routen gesamt im Execute-Router.
