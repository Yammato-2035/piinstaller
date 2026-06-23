# Fix11 Backup List Decouple Contract

## Ausgangslage

- **CI-Fehler:** `test_backup_list_decouple_fix11_v1.py::test_media_path_is_blocked_without_scan`
- **CI-Run:** `28042666012` (rot nach grünem B4–B8 Router-Batch)
- **Security:** grün
- **HEAD (vor Fix):** `96641ab`
- **Preflight staged:** 16 Dateien, unangetastet

## Ursache

**Test veraltet (A)** — kein Codefehler.

`test_media_path_is_blocked_without_scan` suchte `"backup.path_invalid"` in `app.py`. Seit Router-/Handler-Migration liegt die Response-Erzeugung in `core/backup_readonly_handlers.py::list_backups`. Die Validierung `_validate_backup_list_dir` (inkl. `STORAGE-PROTECTION-005` für `/media`) bleibt in `app.py` und wird über `backup_readonly_runtime.validate_backup_list_dir` aufgerufen.

## Architekturentscheidung

| Punkt | Befund |
|---|---|
| `list_backups` | `api/routes/backup_readonly.py` → `backup_readonly_handlers.list_backups` |
| `/media`-Validierung | `app._validate_backup_list_dir` (read-only, kein Scan) |
| `/media` ohne Scan blockiert | **ja** (funktional verifiziert via TestClient) |
| `diagnosis_id` im Response | **ja** (`STORAGE-PROTECTION-005`) |
| Test las noch `app.py` für Handler-Code | **ja** → korrigiert |

## Funktionaler Safety-Check (TestClient)

```
GET /api/backup/list?backup_dir=/media/test
→ 200, code=backup.path_invalid, diagnosis_id=STORAGE-PROTECTION-005, validation_mode=read_only
```

## Geänderte Dateien

- `backend/tests/test_backup_list_decouple_fix11_v1.py`

## Lokale Validierung

- Fix11 + Regression-Gruppe: **29 passed**
- Security-Smoke: pip-audit + npm audit **0 vulnerabilities**

## Erwartetes CI-Ergebnis

- Fix11 grün
- Keine Safety-Abschwächung

## Nach Push

- **Commit:** pending
- **CI-Run / Ergebnis:** pending
