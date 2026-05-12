# Isolierter Restore-Test (Full-Backup)

Datum der Ausführung (System): 2026-04-19 (UTC/lokal je nach Host).

## Voraussetzung Phase 1

| Prüfung | Ergebnis |
|--------|----------|
| Datei `/mnt/backup-test/full-backup.tar.gz` vorhanden | **Nein** (`test -f`: nicht vorhanden) |
| Verzeichnis `/mnt/backup-test` | **Nein** (`ls`: „Datei oder Verzeichnis nicht gefunden“) |
| Unter `/mnt` sichtbar | `backups/` (Verzeichnis), kein `backup-test` |

## Testverzeichnis

| Aktion | Ergebnis |
|--------|----------|
| `mkdir -p /tmp/setuphelfer-restore-test` | **Erfolg** (ohne sudo, Benutzer `volker`) |
| `sudo rm -rf /tmp/setuphelfer-restore-test` | **Nicht ausgeführt** (nicht nötig: Verzeichnis war leer/neu) |

## Phase 2 – Restore (`restore_files`)

Aufruf (Setuphelfer-Backend, `backend/modules/restore_engine.py`):

- `archive_path`: `/mnt/backup-test/full-backup.tar.gz`
- `target_directory`: `/tmp/setuphelfer-restore-test`
- `allowed_target_prefixes`: `(Path("/tmp/setuphelfer-restore-test").resolve(),)`
- `dry_run`: `False`

| Feld | Wert |
|------|------|
| `ok` | **False** |
| `message_key` | `backup_recovery.error.restore_files_failed` |
| `detail` | `[Errno 2] No such file or directory: '/mnt/backup-test/full-backup.tar.gz'` |

Es trat **keine** ungefangene Python-Exception außerhalb der Rückgabe auf; der Fehler kam als Rückgabe-`detail` aus der `tarfile.open`-Ebene.

## Phasen 3–7

**Nicht durchführbar**, weil kein Archiv gelesen werden konnte; unter `/tmp/setuphelfer-restore-test` liegen **keine** extrahierten Dateien (nur das leere Verzeichnis).

Folgende Prüfungen wurden **nicht** ausgeführt (mangels Daten):

- `find … | head -50` (Struktur etc., home, opt, usr)
- Marker `…/opt/setuphelfer-test/marker.txt`
- Testdatei unter `…/home/<user>/testdata/file.txt`
- Symlinks (`etc/alsa/conf.d/50-pipewire.conf`, `etc/alternatives/awk`)
- `sha256sum` + Abgleich mit `MANIFEST.json`
- vollständige Pfadsicherheitsprüfung aller extrahierten Pfade

## Phase 8 – Auffälligkeiten (nur Beobachtung)

1. Der angeforderte Pfad `/mnt/backup-test/full-backup.tar.gz` existiert auf diesem Host **nicht**.
2. Ein alternativer Pfad unter `/mnt/backups/` wurde **nicht** verwendet (Vorgabe war explizit `full-backup.tar.gz` unter `backup-test`).
3. Ziel war ausschließlich `/tmp/setuphelfer-restore-test`; **kein** Restore nach `/` und **keine** Überschreibung von Systempfaden außerhalb des Ziels (Restore ist fehlgeschlagen, bevor etwas extrahiert wurde).

## Zielerreichung (laut Aufgabenstellung)

| Kriterium | Stand |
|-----------|--------|
| Restore ohne Fehler | **Nein** (Archiv fehlt) |
| Struktur vollständig | **Nicht belegbar** |
| Marker / Symlinks / Hash-Stichprobe | **Nicht belegbar** |
| Keine Pfadverletzungen | **Nicht belegbar** (keine extrahierten Dateien) |

---

**Hinweis:** Sobald `/mnt/backup-test/full-backup.tar.gz` auf dem Testrechner existiert, können die Phasen 2–7 mit denselben Parametern wiederholt werden; dieses Dokument beschreibt nur den **tatsächlich** ausgeführten Lauf in dieser Umgebung.
