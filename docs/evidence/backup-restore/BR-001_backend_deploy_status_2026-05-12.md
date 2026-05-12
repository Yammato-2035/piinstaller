# BR-001 — Produktives Backend: Stand, Diff, Deploy (2026-05-12)

## Phase 1 — Erfasste Fakten

| Prüfung | Ergebnis |
|---------|----------|
| Workspace `git rev-parse HEAD` | `03cf7bd43e6bff1f7147ec742d50cf3ceb1b7515` (Stand zum Evidence-Lauf; Arbeitskopie kann zusätzlich lokale Änderungen haben) |
| `curl http://127.0.0.1:8000/api/version` | `install_profile`: **opt**, Version **1.5.0.0** |
| `systemctl show setuphelfer-backend.service` | `User=setuphelfer`, `Group=setuphelfer`, `WorkingDirectory=/opt/setuphelfer`, Start: `/opt/setuphelfer/backend/venv/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port 8000` |
| `systemctl status` | **active (running)** |

## Diff Workspace ↔ `/opt/setuphelfer/backend`

Dateien **verschieden** (`diff -q`):

- `app.py`
- `core/safe_device.py`
- `core/diagnostics/registry.py`
- `core/diagnostics/matcher.py`

## Marker im produktiven `/opt` (grep)

- **`STORAGE-PROTECTION-006`**, **`backup.target_traverse_denied`**, **`_assert_media_tree_traversable`**: im produktiven **`app.py`** / **`safe_device.py`** **nicht** nachweisbar (0 Treffer für 006-Zeichenkette in `safe_device.py`).
- **`_normalize_findmnt_bracket_block_source`**, **`_flatten_findmnt_filesystems`**: im produktiven Bestand **unklar/abweichend** gegenüber Workspace — vollständiger Dateiabgleich nicht nötig für Evidence: **Kern: produktiv veraltet** relativ zu Workspace `03cf7bd`.

## Phase 2 — Deploy / Restart

**Status:** **BLOCKED**

- `sudo -n true` → Passwort erforderlich (`exit 1`).
- **Kein** Kopieren nach `/opt`, **kein** `/tmp/setuphelfer-deploy-backup-*`, **kein** `systemctl restart`.

## target-check strategischer Pfad (produktiv, alter Code)

```text
GET /api/backup/target-check?backup_dir=/media/setuphelfer/setuphelfer-back&create=0
→ STORAGE-PROTECTION-001 (backup.path_invalid)
```

**Hinweis:** Pfad existiert auf dem System nicht; zudem fehlt der Workspace-Diagnosefix auf `/opt`. Nach erfolgreichem Deploy des Workspace-Stands ist bei fehlendem Traverse **`backup.target_traverse_denied`** / **006** erwartbar — weiterhin **blockierend**, aber nicht als „Systemplatte“ fehlklassifiziert.

## Rollback

Nicht anwendbar (kein Deploy).

## Nächste Schritte

1. Interaktives **sudo** mit dokumentiertem Deploy-Runbook (Backup unter `/tmp/setuphelfer-deploy-backup-<ts>/`, `sha256sum`, Kopie der vier Dateien, `systemctl restart setuphelfer-backend.service`).  
2. Erneut **`curl …/api/version`** und **target-check** gegen freigegebenen Pfad.
