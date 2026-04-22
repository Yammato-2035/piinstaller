# Isolierter Restore-Test – erneuter Lauf (Archivpfad + Gast)

## 1. Gefundener Archivpfad (VM-Gast, Port 2222)

Per SSH (`user@127.0.0.1`, Port **2222**), Befehl `ls -la /mnt/backup-test/*.tar.gz`:

| Pfad | Beobachtung |
|------|-------------|
| `/mnt/backup-test/pi-backup-full-20260416_003923.tar.gz` | reguläre Datei, Größe **3895353635** Byte (laut `ls`) |
| `/mnt/backup-test/full-backup.tar.gz` | Symlink → `pi-backup-full-20260416_003923.tar.gz` |

**Auf dem Entwicklungs-Host** (ohne laufende VM): `/mnt/backup-test/` existiert **nicht**; das Archiv liegt nur auf dem Gast (wie in `reports/2026-04-19-backup-setuphelfer-a.md` beschrieben).

## 2. Erster `restore_files`-Versuch (Gast, vor Fix)

- Ziel: `/tmp/setuphelfer-restore-test`
- `allowed_target_prefixes`: `(Path("/tmp/setuphelfer-restore-test").resolve(),)`
- Ergebnis: **`ok=False`**, `detail`: **`unsafe archive path: .`**

Ursache: Tar-Mitglied **`.`** (Wurzelverzeichnis) aus klassischem Root-`tar`; `restore_files` wies es als unsicher ab.

## 3. Code-Anpassung (Repo + Gast)

- In `backend/modules/restore_engine.py`: Platzhalter-Mitglieder **`.`** / **`./`** werden übersprungen (nicht extrahiert), statt den Restore abzubrechen.
- Datei auf den Gast kopiert:  
  `scp -P 2222 …/restore_engine.py user@127.0.0.1:/opt/setuphelfer/backend/modules/restore_engine.py`  
  Exitcode **0**.

## 4. Zweiter Restore-Lauf (Gast, nach Fix)

- Gleiche Parameter wie oben, Archiv: **`/mnt/backup-test/pi-backup-full-20260416_003923.tar.gz`**
- SSH-Sitzung lief ca. **60 Minuten**; in der erfassten Terminal-Ausgabe erschienen **keine** Zeilen `RESTORE_OK=` / `RESTORE_KEY=` / `RESTORE_ERR=` (kein Python-Stdout bis Sitzungsende).
- Abschluss der Shell: `exit_code: unknown` (laut Terminal-Metadaten), **ohne** auswertbare Restore-Rückgabe in dieser Umgebung.

## 5. SSH nach dem Lauf

Mehrere Versuche `ssh … 127.0.0.1:2222` endeten mit:

- `Connection timed out during banner exchange`

Damit sind **Phasen 3–7** (Struktur, Marker, Symlinks, Hash, Pfadliste) in diesem Lauf **nicht** erneut gegen den Gast ausführbar gewesen.

## 6. Lokaler Nachweis (Host, ohne VM)

- Unittest **`test_restore_skips_tar_root_dot_member`**: Archiv mit Mitglied **`.`** plus `hello.txt` → **`restore_files` → `ok=True`**, `hello.txt` unter Ziel vorhanden.
- Gesamtlauf: `python3 -m unittest tests.test_backup_recovery_engines` → **OK** (30 Tests).

## 7. Kurzfassung

| Frage | Antwort |
|--------|---------|
| Richtiger Archivpfad auf dem Gast? | **`/mnt/backup-test/pi-backup-full-20260416_003923.tar.gz`** (Symlink **`full-backup.tar.gz`**) |
| Restore auf Gast nach Fix durchgelaufen? | **In dieser Session nicht belegbar** (kein `RESTORE_*`-Output; danach SSH-Timeout) |
| Blocker vorher? | **Ja** — Mitglied **`.`**; behoben im Repo und auf Gast per `scp` |

**Empfehlung (manuell auf dem Gast, wenn VM wieder erreichbar):** Restore erneut starten; bei Erfolg nacheinander `find`, Marker unter `opt/setuphelfer-test/`, Symlinks unter `etc/`, optional `sha256sum` + Abgleich mit aus dem Archiv extrahiertem `MANIFEST.json` (Restore überspringt `MANIFEST.json` im Zielbaum).
