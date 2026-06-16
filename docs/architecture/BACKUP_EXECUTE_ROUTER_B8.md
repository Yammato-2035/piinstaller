# Backup Execute Router B.8

**Phase:** Monolith-Auflösung — Backup POST-Slice 8 (final core POSTs)  
**Version:** 1.8.10.0

## Scope

| Route | Handler |
|-------|---------|
| `POST /api/backup/create` | `create_backup` |
| `POST /api/backup/verify` | `verify_backup` |
| `POST /api/backup/delete` | `delete_backup` |
| `POST /api/backup/restore` | `restore_backup` |

Nach B.8 enthält `app.py` **keine** `@app.post("/api/backup/…")` mehr. Schwere Logik (`_do_backup_logic`, `_analyze_tar_members`, …) bleibt in `app.py` mit Runtime-Adaptern.

## Tests

`backend/tests/test_backup_execute_router_b8_v1.py` — 18 POST-Routen im Execute-Router.
