# Backup-Manifest und Verify (Setuphelfer)

Technische Referenz: strukturiertes `MANIFEST.json` in jedem Datei-Backup (`*.tar.gz`), Einbettung nach klassischem `tar(1)`-Lauf, und Verify-Logik für reale Linux-Systemarchive.

## Manifest ist verpflichtend

- **`modules/backup_engine.create_file_backup()`** schreibt `MANIFEST.json` als erstes Mitglied ins Archiv und prüft danach mit **`archive_contains_manifest()`**, ob das Mitglied tatsächlich lesbar im `tar.gz` vorhanden ist. Fehlschlag → **`FileBackupResult.ok == False`**, Schlüssel **`K_BACKUP_FAILED_MANIFEST_MISSING`**, das Archiv wird entfernt (kein halbgültiges Artefakt).
- **`embed_manifest_in_tar_gz()`** baut das Manifest aus den Tar-Metadaten neu und ersetzt das Archiv atomar (`os.replace`). Nach dem Schreiben wird erneut geprüft, ob **`MANIFEST.json`** im Archiv existiert. Fehlschlag oder fehlendes Mitglied → Rückgabe `(False, …)` und bei bereits ersetzter Datei wird das fehlerhafte Archiv gelöscht.
- **API (`app._do_backup_logic`)**: Nach **`tar -czf`** nur noch bei **`returncode == 0`** Erfolg; anschließend zwingend **`_embed_manifest_after_tar()`**. Schlägt das Einbetten oder die Verifikation fehl → Status **error**, Code **`backup.failed_manifest_missing`**, **`backup_file: null`**, Archiv per **`_cleanup_backup_file`** entfernt.

**Ein Backup ohne vollständiges, im Archiv nachweisbares `MANIFEST.json` wird nicht mehr akzeptiert.**

## Fail-Fast-Verhalten

- **Kein** „Warning aber success“ mehr für API-Tar-Backups: Returncodes von `tar` außer **0** führen nicht mehr zu einem Erfolgspfad (frühere `_tar_warning_ok` / `_tar_partial_ok` entfernt).
- **Tar-Fehler, Embed-Fehler, fehlendes Manifest, Hashing-/Schreibfehler** in `create_file_backup` → eindeutig **FAILED** (bzw. `ok=False`), optional mit gelöschtem Teilarchiv.
- Ergebnis ist entweder **SUCCESS** oder **FAILED**, kein Zwischenzustand über die öffentliche API der Engine bzw. den beschriebenen Backup-Endpunkt.

## Hardlink-Verifikation

In **`modules.backup_verify.verify_deep`** (mit `verify_checksums=True`):

- Für **`type: hardlink`** wird **`link_target`** auf einen Manifest-Eintrag (Pfad-Schlüssel normalisiert wie im Archiv) abgebildet.
- Das Ziel muss **`type: file`** mit **`sha256`** sein.
- Nach **`extractall`** wird der Inhalt am Hardlink-Pfad per SHA-256 gelesen und mit der **im Manifest gespeicherten Ziel-Datei-Checksumme** verglichen.
- Fehlt das Ziel im Manifest, fehlt die Ziel-Checksumme oder weicht der Inhalt ab → strukturierter Fehler (**`invalid_hardlink`** bzw. **`hash_mismatch`**).

## Archiv-Integrität vor dem Tiefencheck

- **`verify_deep`** und **`verify_basic`** führen für **`*.gz`** zuerst **`gzip -t`** aus. Bei Fehler: sofort **`K_ARCHIVE_CORRUPT`** mit Fehlerart **`gzip_corrupt`** (in `verify_deep` in `details["errors"]`).
- Anschließend Öffnen des Tar, Prüfung der Mitglieder, Einlesen und Parsen von **`MANIFEST.json`**, optional Abgleich Manifest ↔ Archiv-Mitglieder vor der Extraktion.

## Strukturierte Verify-Fehler

`verify_deep` liefert neben `(ok, message_key, details)` in **`details`**:

- **`valid`**: `True` / `False`
- **`errors`**: Liste von Objekten mit mindestens **`kind`**, **`path`**, **`detail`**

Typische **`kind`**-Werte: **`missing_file`**, **`hash_mismatch`**, **`invalid_symlink`**, **`invalid_hardlink`**, **`archive_extra_member`** (nur mit **`strict_archive_manifest=True`**), **`gzip_corrupt`**, **`invalid_manifest_json`**, **`unsafe_archive_member`**.

## Strenger Abgleich Archiv ↔ Manifest (optional)

- Parameter **`strict_archive_manifest`** (Standard **`False`**): Wenn **`True`**, muss jedes Archiv-Mitglied (außer `MANIFEST.json` und GNU-Metadaten) einen passenden Manifest-Eintrag haben; sonst **`archive_extra_member`**.

## Phase 1 – Ist-Analyse (historisch, Kurz)

### Wo wird `tar` erzeugt?

1. **`create_file_backup()`** – `tarfile` mit Manifest zuerst.
2. **`app._do_backup_logic()`** – `tar -czf` für `full` / `incremental` / `data`, danach zwingend **`embed_manifest_in_tar_gz()`**.

### Warum schlug die API-Verify zuvor fehl („gesperrte Einträge“)?

- **`app._analyze_tar_members()`** behandelte u. a. Symlinks/Hardlinks fälschlich als blockiert – das wurde in der Anwendung angepasst (siehe Code/Historie).

## Phase 2 – Manifest-Schema (Version 1)

Top-Level-Felder (JSON):

| Feld | Bedeutung |
|------|-----------|
| `version` | `1` |
| `kind` | `"setuphelfer-backup-manifest"` (`MANIFEST_KIND` in Code) |
| `created_at` | ISO-8601 (UTC), Erzeugungszeitpunkt des Manifests |
| `entries` | Liste von Objekten (siehe unten) |
| `skipped` | Konsolidierte Überspring-Liste (`kind` + Details) |
| `skipped_inputs` | Legacy: übersprungene Top-Level-Eingaben (Strings) |
| `skipped_members` | Legacy: nicht archivierbare Sonderdateien |
| `partition_layout_sfdisk_d` | optional, wie bisher |
| `system` | Metadaten (`uname`, `os_release_snippet`, …) wie bisher |

**Eintrag `entries[]`:**

| Feld | `type=file` | `type=dir` | `type=symlink` | `type=hardlink` |
|------|-------------|------------|----------------|-----------------|
| `path` | Archiv-Pfad relativ ohne führendes `/` | ja | ja | ja |
| `type` | `file` | `dir` | `symlink` | `hardlink` |
| `size` | Byte-Länge als String | — | — | — |
| `sha256` | Hex-Digest | — | — | — |
| `link_target` | — | — | Ziel des Symlinks | Name des verknüpften Archiv-Mitglieds (Hardlink) |

**Legacy:** ältere Manifeste können nur `"files"` statt `"entries"` tragen. Reader: `manifest.get("entries") or manifest.get("files")`.

## Verify / Restore-Anpassungen

- **`modules/backup_verify._validate_archive_members`**: Symlinks und Hardlinks sind **erlaubt**; weiterhin gesperrt: unsichere Pfade, NUL in Linkzielen, Geräte, FIFOs.
- **`verify_deep`**: siehe Abschnitte Hardlink-Verifikation, gzip-Test und strukturierte Fehler.
- **`modules/restore_engine.restore_files`**: Hardlinks werden wie extrahierbare Mitglieder behandelt (siehe dortige Policy).

## API-Backups (`_do_backup_logic`)

Nach **erfolgreichem** `tar` (**nur Returncode 0**) werden Dateirechte angepasst, **`MANIFEST.json`** eingebettet und im Archiv verifiziert. Bei jedem Fehler in dieser Kette wird das Archiv entfernt und ein klarer Fehlercode geliefert (**`backup.failed_manifest_missing`**).

## Keine neuen Abhängigkeiten

Stdlib (`tarfile`, `hashlib`, `json`, `subprocess` für `gzip -t`, …) und bestehende Module.

## FAQ

### Warum wird mein Backup gelöscht?

Wenn **`MANIFEST.json`** nach dem Tar-Lauf **nicht eingebettet** werden kann, **beschädigt** ist oder **im Archiv nicht nachweisbar** ist, gilt das Backup als fehlgeschlagen. Das Setuphelfer entfernt dann die **nicht vertrauenswürdige** `tar.gz`-Datei, damit keine Produktionsumgebung ein Archiv ohne belastbares Manifest irrtümlich als gültig behandelt.

---

## English summary

- **Manifest is mandatory:** `MANIFEST.json` must be present inside the shipped `tar.gz` after embedding; otherwise the run fails and the partial archive is removed.
- **Fail-fast:** No “success with warning” for a broken gzip layer, unreadable manifest, or failed embed step on the documented API backup path—outcome is success or hard failure.
- **Schema:** Same `entries` / legacy `files` rules as in the German sections above; deep verify and restore modules consume this contract.
