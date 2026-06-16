# Backup Execute Router B.7

**Phase:** Monolith-Auflösung — Backup POST-Slice 7  
**Version:** 1.8.9.0

## Scope

| Route | Handler | Router |
|-------|---------|--------|
| `POST /api/backup/clone` | `clone_disk` | `backup_execute` |
| `GET/POST /api/backup/clone/disk-info` | `clone_disk_info` | `backup_readonly` |

Schwere Logik (`_do_clone_logic`, `_clone_disk_info`) bleibt in `app.py`; Handler delegieren über Runtime-Adapter.

## Security

- `clone_disk_info`: Sudo-Passwort wird nur gespeichert, wenn `sudo_store.has_password()` false ist (nicht `get_password()`).
- Antwort enthält kein `sudo_password`-Feld.

## Tests

- `test_backup_execute_router_b7_v1.py` — 14 POST im Execute-Router
- `test_backup_readonly_router_b7_v1.py` — disk-info GET/POST
