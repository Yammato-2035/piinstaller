# Isolierter Restore-Test – Abschlussbericht (setuphelfer-a)

Ausführung per SSH: `volker@127.0.0.1`, Port **2222**. Hostname auf dem Gast: `setuphelfer-a`. Kein Git-Commit.

## Voraussetzungen (Phase 1)

| Prüfung | Ergebnis |
|--------|----------|
| `ls -lh /mnt/backup-test/pi-backup-full-20260416_003923.tar.gz` | **Datei nicht gefunden** (Exitcode `ls` ≠ 0, Meldung „Datei oder Verzeichnis nicht gefunden“). |
| Verfügbares Full-Backup auf dem Gast | `/mnt/backup-test/pi-backup-full-20260420_223625.tar.gz` (laut `ls -la /mnt/backup-test`, reguläre Datei, Größe laut `ls` **3988838366** Byte). |
| `df -h /tmp` | **tmpfs 2,0G**, **100 % belegt** (`Verf. 0`). |
| `df -h /mnt/backup-test` | `/dev/sdc1` **16G**, **ca. 12G verfügbar** (laut Gast-Auszug). |

`sudo rm -rf /tmp/setuphelfer-restore-test` und `mkdir -p /tmp/setuphelfer-restore-test` wurden im Zuge der Versuche ausgeführt; ein vollständiger Restore nach `/tmp` war wegen Speicherplatz nicht möglich (siehe Phase 2).

## Phase 2 – `restore_files` (Backend auf dem Gast)

Arbeitsverzeichnis: `cd /opt/setuphelfer/backend`.

### Versuch A – Ziel `/tmp/setuphelfer-restore-test`

- Aufruf: `restore_files(arch, td, allowed_target_prefixes=(td,))` mit  
  `arch = /mnt/backup-test/pi-backup-full-20260420_223625.tar.gz`,  
  `td = Path("/tmp/setuphelfer-restore-test").resolve()`.
- Rückgabe (Tuple): **`RESTORE_OK= False`**, **`RESTORE_KEY= backup_recovery.error.restore_files_failed`**, **`RESTORE_DETAIL= [Errno 28] No space left on device`**.

### Versuch B – Ziel auf dem Backup-Volume (isolierter Unterordner, nicht `/`)

- Verzeichnis: `/mnt/backup-test/setuphelfer-restore-isolated` (vorher entfernt, neu angelegt, Besitzer `volker:volker`).
- Aufruf: gleiche `arch`, `td = Path("/mnt/backup-test/setuphelfer-restore-isolated").resolve()`, `allowed_target_prefixes=(td,)`.
- Rückgabe: **`RESTORE_OK= True`**, **`RESTORE_KEY= backup_recovery.ok`**, **`RESTORE_DETAIL= None`**.
- Laufzeit der SSH-Sitzung bis Python-Ende: **ca. 106 s** (Shell-Messung).

## Phase 3 – Struktur (unter erfolgreichem Ziel B)

Auszug `find /mnt/backup-test/setuphelfer-restore-isolated -maxdepth 3 | head -50`: u. a. Pfade unter `…/etc/`, `…/boot/`, `…/media/`.

Auszug `ls -la` im Wurzelverzeichnis des Restore-Ziels: u. a. **`bin`**, **`boot/`**, **`etc/`**, **`home`**, **`lib`**, **`lib64`**, **`lost+found/`**, **`media/`**, **`opt/`**, **`root`**, **`sbin`**, **`srv/`**, **`usr/`**, **`var/`** (Symlinks `bin`→`usr/bin`, `lib`→`usr/lib`, …).

## Phase 4 – Marker

| Pfad | Ergebnis |
|------|----------|
| `…/opt/setuphelfer-test/marker.txt` | **Inhalt ausgegeben** (drei Zeilen: `marker_id=setuphelfer-vm-test-001`, `created=2026-04-20T21:09:09+02:00`, Leerzeile). |
| `…/home/user/testdata/file.txt` | **Nicht vorhanden** (`sudo cat`: „Datei oder Verzeichnis nicht gefunden“). |
| `…/home` | Verzeichnis **`d---------`** (Modus **000**), nur `.` und `..` sichtbar (`sudo ls -la`). |

## Phase 5 – Symlinks

| Prüfung | Ergebnis |
|--------|----------|
| `ls -l …/etc/alsa/conf.d/50-pipewire.conf` | **Datei nicht gefunden** (kein solches Mitglied im Archiv, siehe unten). |
| `ls -l …/etc/alsa/conf.d/99-pulse.conf` | Symlink vorhanden: **`…/usr/share/alsa/alsa.conf.d/pulse.conf`** (Ziel absolut). |
| `readlink …/etc/alternatives/awk` | Ausgabe: **`/usr/bin/mawk`**. |

Archiv-Inhalt `tar -tzf … \| grep '^etc/alsa/conf.d/'`: **15** Pfade; darin **kein** `50-pipewire.conf` (u. a. `50-pulseaudio.conf`, `99-pulse.conf`, …).

`tar -tzf … \| grep '^home/user/'`: **keine** Treffer in der Stichprobe (leere Ausgabe).

## Phase 6 – Integrität (Stichprobe)

| Messung | Wert |
|--------|------|
| `sha256sum …/etc/ImageMagick-7/colors.xml` | `df4296cef99a22b5f64eff137b5201ff0394c7805bf3105d5f97f65336867997` |
| Eintrag `path == "etc/ImageMagick-7/colors.xml"` in `MANIFEST.json` im Archiv (Python `tarfile` + `json`) | `sha256` = **`df4296cef99a22b5f64eff137b5201ff0394c7805bf3105d5f97f65336867997`** |

Die beiden Zeichenketten sind **identisch**.

## Phase 7 – Pfadsicherheit

- Kommando: `sudo find /mnt/backup-test/setuphelfer-restore-isolated -print0` → Python prüft Präfix `b"/mnt/backup-test/setuphelfer-restore-isolated"` für jeden Pfad.
- Ausgabe: **`PATH_CHECK_FILES= 306125 bad= 0`**.

## Kurzfassung Zielerreichung (Sollkriterien aus der Aufgabe)

| Kriterium | Erfüllt? | Kurzbeleg |
|-----------|----------|-----------|
| Restore ohne Fehler | **Nur für Ziel B** | `RESTORE_OK=True` nach `/mnt/backup-test/setuphelfer-restore-isolated`; **nicht** für `/tmp` (`ENOSPC`). |
| Struktur (etc/home/opt/usr) | **Ja (Ziel B)** | `ls` im Restore-Wurzelverzeichnis. |
| Marker `opt/setuphelfer-test/marker.txt` | **Ja** | `cat` wie oben. |
| Marker `home/user/testdata/file.txt` | **Nein** | Datei fehlt; `home/user/` nicht im Archiv-Listing. |
| Symlink `50-pipewire.conf` | **Nein** | Weder im Archiv noch im Restore-Baum. |
| Anderer Symlink (Stichprobe) | **Ja** | `99-pulse.conf`, `etc/alternatives/awk` → `/usr/bin/mawk`. |
| Hash-Stichprobe | **Ja** | `colors.xml` = Manifest-SHA256. |
| Keine Pfadverletzungen | **Ja (Ziel B)** | `bad= 0` bei 306125 Pfaden. |

## Hinweise ohne zusätzliche Interpretation

- Das in der Aufgabe genannte Archiv **`pi-backup-full-20260416_003923.tar.gz`** war auf dem Gast **nicht** auffindbar; verwendet wurde **`pi-backup-full-20260420_223625.tar.gz`**.
- Ein Restore unter **`/tmp/setuphelfer-restore-test`** scheiterte an **`[Errno 28] No space left on device`** bei vollem **2 GiB-tmpfs**.
- Es wurde **kein** Restore nach `/` durchgeführt; das Ziel lag unterhalb von `/mnt/backup-test/…` bzw. (fehlgeschlagen) `/tmp/…`.
