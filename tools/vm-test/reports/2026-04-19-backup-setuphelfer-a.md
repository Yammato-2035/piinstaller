# Backup-Report setuphelfer-a (Phase 3)

Ausführung per SSH auf dem Gast (`user@127.0.0.1`, Port **2222**). Hostname auf dem Gast: `debian`. Kein Git-Commit.

## 1. Backup-Ziel (Device + Mount)

Auszug `lsblk -f` (Gast):

- `sdb1`: `FSTYPE=ext4`, `UUID=3e0b943b-d148-492c-b204-671a8026572b`, Mountpoint `/mnt/backup-test`.

Auszug `findmnt -J /mnt/backup-test` (Gast):

- `target`: `/mnt/backup-test`
- `source`: `/dev/sdb1`
- `fstype`: `ext4`
- `options`: `rw,relatime`

Auszug `mount | grep /mnt/backup-test` (Gast):

- `/dev/sdb1 on /mnt/backup-test type ext4 (rw,relatime)`

Auszug `df -h /mnt/backup-test` (nach Backup, Gast):

- `Filesystem /dev/sdb1`, `Size 7.8G`, `Used 3.7G`, `Avail 3.8G`, `Use% 50%`, `Mounted on /mnt/backup-test`

Hinweis API `GET /api/backup/target-check?backup_dir=/mnt/backup-test` (ohne `create`): lieferte u. a. `write_test.success: false` (User-Schreibtest) und `mount` mit `fstype: overlay` und `target: /` (von der API geliefert). Unmittelbar vor dem Backup startete die Erstellung trotzdem (siehe Abschnitt 5).

## 2. Backup-Datei (Größe, Pfad)

Vom Setuphelfer erzeugt (async Job `353465c0deb8`):

- Pfad: `/mnt/backup-test/pi-backup-full-20260416_003923.tar.gz`
- Größe laut Job-Endzustand: `bytes_current` **3895353635** (im Job-JSON dokumentiert).
- `ls -lh` auf dem Gast: **3.7G**, Besitzer `user:user`.

Symlink (neu angelegt, Zieldatei unverändert; kein Überschreiben einer bestehenden `full-backup.tar.gz`):

- `/mnt/backup-test/full-backup.tar.gz` → `pi-backup-full-20260416_003923.tar.gz` (relative Symlink-Zielangabe).

## 3. Archivstruktur (Auszug)

Auszug `tar -tzf … | head -50` (Gast, erste Zeilen):

- `./`, `bin`, `boot/` mit Kernel-Dateien, `etc/` mit u. a. `etc/ImageMagick-7/`, `etc/NetworkManager/`, `etc/X11/`, …

Anzahl Einträge `tar -tzf … | wc -l` (Gast): **306367**.

`gzip -t` auf dem Archiv (Gast): Exitcode **0**.

Gezielte Mitgliedsprüfung (Gast):

- `tar -tzf … opt/setuphelfer-test/marker.txt`: Mitglied **vorhanden** (eine Zeile ausgegeben).
- `tar -tzf … home/user/testdata/file.txt`: Meldung **Not found in archive** (tar Exitcode 2 wegen fehlendem zweiten Mitglied in derselben Aufrufliste).

`tar -tzf … | grep -i MANIFEST | head -5` (Gast): Treffer nur unter `opt/setuphelfer/frontend/...` (Dateinamen mit „manifest“ im Pfad), **kein** `MANIFEST.json` im Archivwurzelbereich in den ersten fünf Treffern.

## 4. Verify-Ergebnis (Setuphelfer-API)

Endpunkt: `POST http://127.0.0.1:8000/api/backup/verify`  
`backup_file`: `/mnt/backup-test/pi-backup-full-20260416_003923.tar.gz`

### basic

- `status`: `error`
- `api_status`: `error`
- `message`: `Backup-Archiv enthält gesperrte Einträge (Traversal, absolute Pfade, Symlinks, Hardlinks oder Sonderdateien).`
- `data.results.valid`: `false`
- `data.results.blocked_entries` (Auszug, Reihenfolge wie API): beginnt mit `bin`, gefolgt von mehreren Pfaden unter `etc/alsa/conf.d/` und `etc/alternatives/…`.

### deep

- Gleiche Felder wie bei **basic** (`status`/`api_status`/`message`/`valid`/`blocked_entries`-Anfang identisch zum abgerufenen JSON-Auszug).

## 5. Auffälligkeiten / Fehler

- **systemd-Dienst `setuphelfer-backend`**: Mit der ausgelieferten Unit ließ sich das Backup zunächst nicht starten (`backup.mkdir_failed` / sudo-Fehler). Auf dem Gast wurde ein Drop-In ergänzt: `/etc/systemd/system/setuphelfer-backend.service.d/mnt-backup.conf` mit u. a. `ReadWritePaths=/mnt/backup-test`, `NoNewPrivileges=no`, `PrivateDevices=no`, `CapabilityBoundingSet=…` (siehe Datei auf dem Gast). Danach: `daemon-reload` und `restart` des Dienstes. Anschließend akzeptierte `POST /api/backup/create` den async-Job.
- **Job-Ende**: `job.status` = `success`, aber `severity` = `warning`, Meldung sinngemäß Backup erstellt, **tar** lieferte **Returncode `None`** (Text im Job-JSON). Zusätzlicher Hinweistext: möglicherweise unvollständig.
- **`/api/backup/verify`**: Für dieses Full-System-Archiv liefern **basic** und **deep** `valid: false` mit gesperrten Einträgen (siehe Abschnitt 4).
- **Pfad `home/user/testdata/file.txt`**: In der gezielten `tar`-Mitgliedsprüfung nicht als Archivmitglied gefunden (siehe Abschnitt 3).
- **API `target-check`**: `storage_validation`-Block mit `ok: true` erschien in der abgerufenen Antwort (ohne `create`) nicht; stattdessen `write_test.success: false` und `code`: `backup.target_not_writable` (siehe Abschnitt 1).

## 6. Marker-Dateien (Vorbereitung)

Auf dem Gast vorhanden (Prüfung vor Backup, nicht erneut überschrieben):

- `/opt/setuphelfer-test/marker.txt`
- `/home/user/testdata/file.txt`
