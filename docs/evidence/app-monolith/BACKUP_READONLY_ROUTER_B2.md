# Backup Readonly Router B.2

**Kampagne:** A.4 · **Version:** 1.7.15.0

## Metriken

| Kategorie | Anzahl |
|-----------|--------|
| Backup-Routen gesamt (app+router) | ~30 |
| readonly extrahiert | **12** |
| execute/write in app | ~18 |
| readonly verbleibend in app | target-check (Schreibtest) |

## Extrahierte GETs

`/status`, `/settings`, `/jobs`, `/jobs/{id}`, `/jobs/{id}/evidence`, `/cloud/list`, `/cloud/quota`, `/targets`, `/external-targets`, `/profiles`, `/usb/info`, `/list`

## Module

- `backend/api/routes/backup_readonly.py`
- `backend/core/backup_readonly_handlers.py`
- `backend/core/backup_readonly_runtime.py`

## Nicht extrahiert

create, restore, clone, usb mount/prepare/eject, verify POST, delete POST, target-prepare, target-check (write side-effects)
