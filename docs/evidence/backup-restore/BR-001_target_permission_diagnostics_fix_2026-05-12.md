# BR-001 — Target-Check: Berechtigungsdiagnose (Workspace-Fix)

**Datum:** 2026-05-12  
**Commit-Message (Workspace):** `Fix backup target-check permission diagnostics` — vollständigen Hash lokal mit `git log -1 --oneline` ermitteln.
**Modus:** STRICT — nur Code/Doku/Evidence im Repo; **kein** Backup, **kein** Restore, **kein** Deploy, **kein** `systemctl restart`, **kein** alternativer Zielpfad (insbesondere **kein** `/mnt/setuphelfer/backups`), **kein** Bind-Mount.

## Verbindlich freigegebener Pfad

**`/media/gabriel/setuphelfer-back`** — unverändert einziger BR-001-Zielpfad laut Betreiberpolitik.

## Erkannte Ursache (Analyse, unverändert)

Wenn der Dienstnutzer **`setuphelfer`** ein Parent-Verzeichnis unter **`/media/…`** oder **`/run/media/…`** nicht traversieren kann, lieferte die bisherige Logik nach Anker-Fallback eine Mount-Zuordnung zur **Root-Partition** und klassifizierte das Ziel fälschlich als **STORAGE-PROTECTION-001** („Systemplatte“). Shell-`findmnt` auf dem vollen Pfad zeigte weiterhin korrekt z. B. **`/dev/sda1`**.

Siehe weiterhin: **`BR-001_productive_target_check_media_path_analysis_2026-05-12.md`**.

## Geänderter Codepfad (minimal)

| Bereich | Datei | Inhalt |
|---------|-------|--------|
| Traversierung / Validierung | `backend/core/safe_device.py` | Vor `resolve()` / in `resolve_mount_source_for_path`: explizite Traversierbarkeit im Media-Baum; bei **PermissionError** / **EACCES**/**EPERM** → **`STORAGE-PROTECTION-006`** (`_DIAG_TRAVERSE_DENIED`), kein stiller Fallback auf Root-Anker für diesen Fall; analog **`OSError`** nach fehlgeschlagenem `Path.resolve()` bzw. Anker-Auflösung. |
| API target-check | `backend/app.py` | Bei Validierungsfehler mit **006**: Response-Code **`backup.target_traverse_denied`**, `details.diagnosis_id` **`STORAGE-PROTECTION-006`**, `details.reason` ohne doppeltes Präfix. |
| Diagnosekatalog | `backend/core/diagnostics/registry.py`, `matcher.py` | Fall **STORAGE-PROTECTION-006** registriert/abgeglichen. |
| Tests | `backend/tests/test_backup_target_permission_diagnostics_v1.py` | Mocks: **006** statt **001** bei simuliertem Traverse-Verlust; Root bleibt **001**; erlaubtes Präfix unter `/tmp` unverändert; **target-check**-API liefert **`backup.target_traverse_denied`** (kein Backup-Start). |
| Regression | `backend/tests/test_safe_device_storage_protection_v1.py` | Patch von `_assert_media_tree_traversable` für bestehenden Media-/Block-Testpfad. |

## Neuer Diagnosegrund

- **ID:** **`STORAGE-PROTECTION-006`**
- **API-Code (target-check):** **`backup.target_traverse_denied`**
- **Semantik:** Ziel weiterhin **blockiert** / nicht „erlaubt“ — aber **nicht** mehr als Systemplatte fehlklassifiziert.

## Warum Safety nicht abgeschwächt wurde

- Keine Erweiterung der Allowlist, kein neuer Schreibpfad.
- **006** ist weiterhin ein harter Schreibschutz-Fehler; Backup-Start bleibt unmöglich, bis Traversierung und übrige Gates erfüllt sind.

## Tests (lokal)

```bash
cd backend && PYTHONPATH=. venv/bin/python -m pytest \
  tests/test_backup_target_permission_diagnostics_v1.py \
  tests/test_safe_device_storage_protection_v1.py \
  tests/test_preflight_backup_v1.py -q
```

Optional: `venv/bin/python -m pytest tests -q`.

## Produktiv-Nachweis

**Nicht erneut ausgeführt** in diesem Lauf (keine Deploy-/Restart-Freigabe). Erwartung nach Angleichung von `/opt` an diesen Workspace-Stand: **006** / **`backup.target_traverse_denied`** statt **001**, solange Traverse zu **`/media/gabriel`** für den Dienst fehlt.

## Abnahme (Workspace)

| Kriterium | Erfüllt? |
|-----------|----------|
| Keine Pfadumdeutung | **Ja** |
| Kein `/mnt/setuphelfer/backups` | **Ja** |
| Kein Backup gestartet | **Ja** |
| Nicht traversierbar → nicht **001** „Systemplatte“ | **Ja** (Code + Unit-Tests) |
| Safety blockierend | **Ja** |
