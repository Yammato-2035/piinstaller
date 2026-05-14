# Backup-Ziel: Schreib-E/A-Fehler (EIO) während `tar`/`gzip`

**Diagnose-ID:** `BACKUP-IO-ERROR-050`  
**API-Code (Runner):** `backup.write_io_error`  
**Abort-Reason:** `target_write_io_error`

## Symptome

- `gzip: stdout: Input/output error`
- `tar: …tar.gz.partial: Wrote only X of Y bytes`
- `tar: Child returned status 1` / `subprocess_returncode: 2`
- Unvollständige `.partial`-Datei; **kein** finales `.tar.gz`

## Einordnung

Typischerweise **Kernel-/Blockschicht** (`EIO`) auf dem **Zielgerät** (USB-Brücke, SATA, defekte Sektoren, instabile Stromversorgung), **nicht** Anwendungslogik des Setuphelfer-Codes. `errors=remount-ro` in den Mount-Optionen von ext4 kann nach Fehlern ein **read-only**-Remount nach sich ziehen — dann schlagen weitere Schreibversuche fehl.

## Empfohlene Schritte (Operator)

1. **`dmesg`** / **`journalctl -k`** zum Zeitpunkt des Fehlers prüfen (USB-Reset, `I/O error`, `Buffer I/O error`, ext4-Fehler).
2. **Kabel / Hub / Strom** (Y-Kabel, zu schwaches Netzteil) am externen Medium prüfen.
3. **`findmnt`**, **`lsblk`**, **`smartctl`** (wenn zutreffend) — **keine** Formatierung ohne ausdrückliche Freigabe.
4. **`GET /api/backup/target-check?backup_dir=…&create=0`** erneut ausführen, nachdem Hardware/Mount stabil ist.
5. **Nicht** die `.partial` als Archiv für **Verify** oder **Restore** verwenden.

## Verweise

- Evidence: `docs/evidence/backup-restore/BR-001_write_io_error_2026-05-14.md`
- Testmatrix: **BR-013** in `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`
