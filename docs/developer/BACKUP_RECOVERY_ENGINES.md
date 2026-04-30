# Backup- und Recovery-Engines (Worst-Case / Full-Recovery)

Technische Referenz zu den Python-Modulen für Rohabbilder, Dateiarchive, Verifikation, Restore und Recovery-Transport – ergänzend zur UI unter **Backup & Restore**.

## Module (Backend)

| Bereich | Datei | Kurzbeschreibung |
|--------|--------|------------------|
| i18n (Schlüssel) | `backend/core/backup_recovery_i18n.py` | Stabile Meldungsschlüssel und `tr()`; Standardtexte in `DEFAULT_CATALOG` (ersetzbar). |
| Blockgeräte | `backend/core/block_device_allowlist.py` | Nur Whole-Disk-Muster (`/dev/sd[a-z]`, `/dev/nvme…`, `/dev/mmcblkN`). |
| Pfade | `backend/core/backup_path_allowlist.py` | Backup-/Restore-Pfade nur unter konfigurierten Präfixen. |
| Engine | `backend/modules/backup_engine.py` | `create_image_backup`, `create_file_backup`, `create_manifest`, `embed_manifest_in_tar_gz` (SHA-256, optional `sfdisk -d`, Metadaten; siehe [BACKUP_MANIFEST.md](./BACKUP_MANIFEST.md)). |
| Speicher / Mount | `backend/modules/storage_detection.py` | `lsblk`/`blkid`/`findmnt`: Geräteerkennung und **Pflicht**-Validierung des Datei-Backup-Ziels vor `create_file_backup`. |
| Verifikation | `backend/modules/backup_verify.py` | `verify_basic`, `verify_deep` (Extraktion unter `/tmp/.../setuphelfer_verify/`). |
| API-Verify (Deep) | `backend/app.py` (`POST /api/backup/verify`, `mode=deep`, unverschlüsselte `.tar.gz`) | Ruft `verify_deep` auf: **MANIFEST.json** im Archiv, parsbar; SHA-256 der Dateieinträge gegen Manifest; gzip-Test bei `.gz`. |
| Restore | `backend/modules/restore_engine.py` | `restore_partition_table`, `restore_image`, `restore_files`, `install_bootloader` (nur erlaubte Geräte). |
| Symlink-Policy | `backend/modules/backup_symlink_safety.py` | Prüfung relativer Symlink-Ziele gegen Pfadflucht aus dem Restore-/Verify-Wurzelverzeichnis. |
| Transport | `backend/modules/recovery_transport.py` | `auto_mount_usb`, `connect_webdav`, `download_backup` (curl, keine Paketinstallation). |
| Verschlüsselung | `backend/modules/backup_crypto.py` | AES-256-GCM (`cryptography`); **Schlüssel nie im Archiv**. |
| Recovery-CLI | `recovery/main.py` | Menü bei defektem Root-System (USB/WebDAV/Diagnose-Hinweis). |

## Sicherheit und Grenzen

- **Kein** automatisches Installieren von Paketen (z. B. `grub-install` muss vorhanden sein).
- **Destruktive** Befehle (`dd`, `sfdisk`) nur nach expliziter Allowlist-Prüfung.
- **Bootfähigkeit** nach Restore auf echter Hardware ist **manuell** nachzuweisen; automatisierte Tests arbeiten nur in temporären Verzeichnissen (`backend/tests/test_backup_recovery_engines.py`).

## Storage Validation / Mount Safety

**Warum nötig:** Ohne Mount-Prüfung kann ein Datei-Backup still auf dem **Root-Dateisystem**, unter **tmpfs** oder auf einem **Live-Medium** landen – obwohl der Nutzer ein „USB-Laufwerk“ meint. Die Allowlist (`backup_path_allowlist`) schützt nur vor Pfaden **außerhalb** freigegebener Präfixe, nicht vor dem **physischen/logischen Speicherort** dahinter.

**Typische Fehler:**

- Zielordner liegt unter `/` (oder auf derselben Mount-Instanz wie `/`) statt auf einem separaten Datenträger.
- Ziel ist nicht eingehängt (`findmnt` liefert keinen Eintrag).
- Quelle im `findmnt`-Sinne ist kein lokales Blockgerät (`tmpfs`, `nfs`, …).
- Dateisystem ist ungeeignet (z. B. `squashfs`/`iso9660`/`overlay` oder nicht `ext4`/`xfs`/`ntfs`).

**Verhalten im Fehlerfall:** `create_file_backup` bricht **vor** dem Packen ab und liefert `FileBackupResult(ok=False, …)` mit einem stabilen i18n-Schlüssel aus `backup_recovery_i18n` (z. B. `backup_recovery.error.backup_target_root_filesystem`). Es werden keine Archivdateien angelegt.

**FAQ: Warum verweigert Setuphelfer mein Backup-Ziel?** Wenn das Zielverzeichnis auf dem Root-Dateisystem liegt, nicht gemountet ist, kein `/dev/…`-Blockgerät dahintersteht oder das Dateisystem nicht ausdrücklich erlaubt ist, wird das Backup abgelehnt. Wähle ein eingehängtes externes Volume (z. B. unter `/media` oder `/mnt`) mit **ext4**, **xfs** oder **ntfs**.

## Backup Target Permissions

**Ziel:** Datei-Backups sollen auf einem **separaten** Datenträger landen, ohne dass jeder Schreibzugriff hat (`chmod 777`) und ohne vor jedem Lauf manuelles `chown`.

**Empfohlenes Modell**

- Systemgruppe **`setuphelfer`** (wird bei Installation angelegt, sofern noch nicht vorhanden).
- Mount-Punkt des Backup-Volumes: **`root:setuphelfer`**, Modus **`0770`** (nur root und Gruppe `setuphelfer`, kein World-Write).
- Der **Backend**-Dienst (`setuphelfer-backend.service`) erhält **`SupplementaryGroups=setuphelfer`**, damit der API-Prozess (typisch der Installations-User oder `setuphelfer`) die Gruppenrechte des Kernels nutzen kann — **ohne** die primäre `Group=` des Dienstes zu verändern (Dateien unter `/opt/setuphelfer` bleiben konsistent zum Install-User).
- **`ReadWritePaths`** enthält `/mnt`, **`/mnt/setuphelfer`** und übliche State-Pfade, damit das Standard-Backupziel erreichbar ist.
- **Tar-Packen** (`_do_backup_logic` in `app.py`) läuft als Dienstnutzer **ohne sudo**; die Backend-Unit setzt **`NoNewPrivileges=true`**, damit der Laufzeitpfad mit systemd-Härtung konsistent bleibt (vgl. FIX-1 / HW1-01..05).

**Prüfung vor dem Backup:** Nach der Mount-/Dateisystem-Validierung führt `validate_backup_target` einen **echten Schreibtest** im Archiv-Elternverzeichnis aus (kurzlebige Probedatei). Schlägt dieser fehl, bricht die Engine mit dem stabilen Schlüssel `backup_recovery.error.backup_target_not_writable` ab — **ohne** automatisches `chown`/`chmod` im Normalbetrieb.

**Optional (nur kontrollierte Test-VMs):** Wenn die Umgebungsvariable **`SETUPHELFER_FIX_PERMISSIONS=1`** gesetzt ist, versucht das Backend **einmalig** vor der Validierung (mit `sudo`), das gewählte Backup-Verzeichnis auf `root:<SETUPHELFER_BACKUP_GROUP oder setuphelfer>` und `0770` zu setzen, und protokolliert das deutlich im Log. Standardmäßig ist das deaktiviert.

**FAQ: Warum funktioniert mein Backup nicht ohne Schreibrechte?** Wenn das Ziel **`root:root`** mit **`0755`** gemountet ist, kann der Dienst dort nicht schreiben — früher wurde oft `sudo tar` genutzt. **Aktuell:** Tar läuft ohne sudo; stattdessen Mount-Punkt **einmalig** als Administrator auf **`root:setuphelfer`** und **`0770`** setzen (oder `in-guest-prepare-backup-disk.sh` mit `VMTEST_BACKUP_OWNER_GROUP=setuphelfer`). Optional nur in Test-VMs: `SETUPHELFER_FIX_PERMISSIONS=1` für ein einmaliges sudo-chown durch das Backend.

## Post-Restore Verhalten

Nach einem Datei-Restore auf eine Zielsystemplatte und anschließendem Boot sind für Setuphelfer **keine manuellen Service-Overrides** vorgesehen.

Erwarteter Zustand nach `install-system.sh`:

- `setuphelfer-backend.service` und `setuphelfer.service` werden aus den Repo-Templates nach `/etc/systemd/system/` geschrieben.
- Alte manuelle Overrides (z. B. `setuphelfer.service.d/override.conf`) werden entfernt.
- Der Installer führt `systemctl daemon-reexec` + `daemon-reload` aus, aktiviert beide Units und validiert, dass beide `active` werden (sonst Exit mit Fehler).
- Die Web-UI-Unit enthält dauerhaft `Environment=NODE_OPTIONS=--max-old-space-size=1024` und benötigt keine ad-hoc Shell-Exports.
- Laufzeitpfade `/opt/setuphelfer`, `/etc/setuphelfer`, `/var/log/setuphelfer`, `/var/lib/setuphelfer` werden vom Installer erstellt, bevor Services starten.

**FAQ: Warum startet Setuphelfer nach Restore nicht?**

Typische Ursachen sind nicht der Restore selbst, sondern ein unvollständiger Zielzustand:

- Setuphelfer wurde auf dem gebooteten Zielsystem noch nicht installiert (`/opt/setuphelfer` fehlt).
- systemd lädt noch alte Unit-Stände (kein `daemon-reexec`/`daemon-reload` nach Service-Dateiwechsel).
- Frontend-Prod-Build fehlt und wird erst beim Service-Start versucht; auf kleinen Systemen kann das in OOM enden.
- Manuelle Overrides aus früheren Tests überlagern aktuelle Unit-Defaults.

Der vorgesehene Weg ist daher immer: `install-system.sh` auf dem gebooteten Zielsystem einmal durchlaufen lassen; danach müssen beide Services ohne manuelle Nacharbeit stabil starten.

## Backup-Modelle (Ist-Stand)

- **Image-basiert:** `create_image_backup` erzeugt ein Rohabbild per `dd` für allowlist-fähige Whole-Disk-Geräte.
- **File-basiert:** `create_file_backup` archiviert Dateien und Verzeichnisse rekursiv als `tar.gz` (nach Allowlist- und **Mount-/Gerätevalidierung** des Archivpfads).
- **Hybrid:** Manifest kann parallel Dateichecksummen und `sfdisk -d`-Layout enthalten, ersetzt aber keinen echten Boot-Nachweis.

## Data-Scope (FIX-3 / FIX-5 / FIX-6)

- `type=data` ist ein **nicht-privilegierter** Backup-Typ für reproduzierbare Läufe ohne sudo.
- Quellen sind bewusst begrenzt auf lesbare Datenpfade im **Dienstkontext**: verpflichtend nur das Home des **effektiven Service-Users** (`pwd.getpwuid(os.geteuid()).pw_dir`), optional `/var/www` wenn lesbar.
- Es gibt **kein** Scannen von `/home/*` und keine automatische Aufnahme fremder Benutzer-Homes.
- Für HW-/Lab-Tests kann der Data-Scope explizit gesetzt werden über `SETUPHELFER_DATA_BACKUP_SOURCES` (z. B. `/mnt/setuphelfer/test-data`).
- Wenn `SETUPHELFER_DATA_BACKUP_SOURCES` gesetzt ist, ersetzt diese Liste die Default-Pflichtquelle (Service-Home) vollständig.
- Konfigurierte Data-Quellen werden nur akzeptiert, wenn sie unter der Allowlist-Wurzel `/mnt/setuphelfer` liegen; `/opt/*` bleibt strikt ausgeschlossen.
- **Nicht Teil von `type=data`:** systemweite/root-only Bereiche wie Container-Runtime (`/opt/containerd`), pauschales `/opt`, Full-System-Kontext.
- Nicht lesbare **optionale** Quellen werden als `skipped_sources` dokumentiert; nicht lesbare **Pflicht**quellen führen deterministisch zu `backup.source_permission_denied` mit `diagnosis_id=BACKUP-SOURCE-PERM-032` (kein ungemapptes `backup.error` nur wegen Home-Read-Rechten).
- Für umfassende System-/Root-/Container-Sicherungen ist ein anderer Backup-Typ/Modus nötig (`full`/systemnah), nicht `type=data`.

## Runtime-Source-Trace (FIX-4)

- Für `type=data` wird vor dem Tar-Lauf strukturiert geloggt: `backup_type`, `target`, `selected_sources`, `skipped_sources`, `required_sources`, `optional_sources`.
- Zusätzlich wird das effektive Tar-Kommando als `effective_tar_command` geloggt (nur Pfade/Klassifikation, keine personenbezogenen Inhalte).
- `type=data` nutzt ausschließlich `_plan_data_backup_sources`; ein Fallback auf die alte harte Liste (`/home /var/www /opt`) ist im API-Pfad entfernt.
- Das gleiche Data-Source-Planning ist auch im eingebetteten Scheduler-Runner aktiv (`plan_data_backup_sources`), damit Runtime- und API-Pfad konsistent bleiben.

## File-Engine (korrigierter Stand)

- Verzeichnisse werden rekursiv gesichert; reguläre Dateien bleiben unterstützt.
- Archivpfade sind relativ zum Root-Kontext (`/etc/hosts -> etc/hosts`), keine flachen `p.name`-Einträge mehr.
- Kollisionsschutz ist aktiv: doppelte Zielpfade im Archiv führen zu sauberem Abbruch.
- Überlappende Eingaben (`/home` plus `/home/user/...`) werden nicht doppelt archiviert; übersprungene Eingaben stehen im Manifest unter `skipped_inputs` und zusätzlich konsolidiert unter `skipped` (siehe [BACKUP_MANIFEST.md](./BACKUP_MANIFEST.md)).
- Manifest-Dateiliste: **`entries`** (Schema Version 1); ältere JSONs können nur **`files`** enthalten – Reader sollten `entries` bevorzugen.
- **Symlinks:** werden als Symlinks ins Archiv übernommen (**ohne** Dereferenzierung beim `tar`-Add), damit typische Linux-Bäume wie `/etc` (z. B. `alsa/conf.d/*.conf`) nicht mehr am Backup scheitern.
- **Sonderdateien** (Sockets, FIFOs, Geräte usw.): werden beim rekursiven Sammeln **nicht** archiviert und im Manifest unter `skipped_members` dokumentiert (kein Abbruch des gesamten Laufs wegen eines einzelnen Sockets).
- Archivpfad-Ermittlung nutzt bewusst **kein** `Path.resolve()` auf Quellpfaden, damit logische Pfade erhalten bleiben (kein stilles Wegfolgen von Symlinks bei der Namensgebung).

## Verify/Restore (korrigierter Stand)

- `verify_basic` prüft unsichere **Member-Namen** (Traversal, absolute Pfade); symbolische Links im Archiv sind erlaubt, Hardlinks/FIFOs/Geräte-Einträge weiterhin blockiert.
- `verify_deep` extrahiert mit `filter="tar"` (falls verfügbar), damit Symlinks nicht materialisiert werden; Manifest-Einträge nutzen `type` (`file`/`dir`/`symlink`) und bei Symlinks `link_target`. Für Symlink-Leafs wird kein `Path.resolve()` verwendet (sonst würde der Symlink fälschlich aufgelöst).
- `restore_files` erlaubt symbolische Links, sofern relative Ziele nach `..`-Auflösung im Restore-Wurzelverzeichnis verbleiben; absolute Symlink-Ziele werden für reale Systembäume zugelassen (Risiko beim späteren **Folgen** des Links bleibt). Hardlinks/FIFOs/Geräte bleiben gesperrt; `MANIFEST.json` wird nicht ins Ziel geschrieben.

### Verify Deep (API, `mode=deep`, unverschlüsselte `.tar.gz`)

Nach den Archiv-Member-Sicherheitschecks (`_analyze_tar_members` in `app.py`) nutzt die **HTTP-Verify**-Route für unverschlüsselte `.tar.gz` dieselbe Logik wie die Engine:

1. **Manifestprüfung:** `MANIFEST.json` muss im Tar enthalten und gültiges JSON sein; fehlt oder ist unlesbar → API-Code **`backup.failed_manifest_missing`**, typische Diagnose **`BACKUP-MANIFEST-001`** (in `details.diagnosis_id`, wenn gesetzt).
2. **SHA-256-Validierung:** Für Dateieinträge im Manifest werden Checksummen nach Extraktion in einer Sandbox mit den Archiv-Inhalten verglichen; Abweichung → **`backup.verify_integrity_failed`**, Diagnose **`BACKUP-HASH-003`** bei Hash-Mismatch.
3. **Gzip/Tar-Lesefehler:** `gzip -t` bzw. Lesen/Extrahieren schlägt fehl → **`backup.verify_archive_unreadable`**, Diagnose oft **`BACKUP-ARCHIVE-002`**.

### Restore Path Security (`_analyze_tar_members` / Preview)

- **Problem:** Ein naiver Pfadcheck mit `name.lstrip("./")` kann **`../../../tmp/evil`** fälschlich zu **`tmp/evil`** „kollabieren“, weil `lstrip` eine **Zeichenklasse** entfernt (alle führenden `.` und `/`), nicht nur ein `./`-Präfix.
- **Fix:** Segmentbasierte Erkennung von **`..`** in Pfadkomponenten plus die übrigen Regeln (absolute Pfade, `/../` in normalisierten Pfaden).
- **Risiko:** **Path Traversal** oder absolute Pfade im Archiv → Restore-Preview bricht mit **`backup.restore_blocked_entries`** ab, **`details.diagnosis_id`** typisch **`RESTORE-PATH-004`**; kein Extrahieren nach außerhalb der Sandbox.

### Fehlerklassifikation: API-Code → Diagnose-ID (Auszug, HW1-03)

| API-`code` (Beispiel) | Typische `details.diagnosis_id` / Matcher |
|----------------------|---------------------------------------------|
| `backup.failed_manifest_missing` | `BACKUP-MANIFEST-001` |
| `backup.verify_integrity_failed` | `BACKUP-HASH-003` (bei `hash_mismatch` in Engine-Details) |
| `backup.verify_archive_unreadable` | `BACKUP-ARCHIVE-002` (u. a. gzip/tar/kaputtes Archiv) |
| `backup.path_invalid` (Storage) | z. B. `STORAGE-PROTECTION-005` im `details.reason` |
| `backup.backup_target_not_writable` | z. B. `PERM-GROUP-008` bei EACCES auf Schreibprobe |
| `backup.restore_blocked_entries` | `RESTORE-PATH-004` |

Vollständige Katalogtexte: `docs/knowledge-base/diagnostics/DIAGNOSIS_CATALOG.md` und Registry `backend/core/diagnostics/registry.py`.

### API-Konsistenz (FIX-9)

- **`GET /api/backup/list`** nutzt jetzt eine eigene **read-only Validierung** (`_validate_backup_list_dir`) statt der Schreibprüfung aus Create:
  - gleiche Mount-Auflösung über `resolve_mount_source_for_path` (autofs/systemd-automount -> reales Blockdevice),
  - keine unnötige Schreibprobe beim reinen Listen,
  - strukturierte Fehlerdetails bei `backup.path_invalid`: `mount_source_seen`, `resolved_source`, `fstype`, `target`, `diagnosis_id`.
- **`POST /api/backup/create` (`type=data`)** liefert die Source-Planung jetzt auch im Erfolgsfall unter `details`:
  - `selected_sources`
  - `skipped_sources`
  - `required_sources`
  - `optional_sources`
- **`POST /api/backup/restore` (`mode=preview`)** ergänzt PrivateTmp-Kontext im Response:
  - `private_tmp_isolation`
  - `preview_dir_visibility_note`
  - `service_private_tmp_hint` (`backup.messages.preview_private_tmp_hint`)

### `GET /api/backup/list` Stabilisierung (FIX-10)

- Endpoint bleibt strikt **read-only**:
  - Pfadprüfung ohne Schreibprobe,
  - `/media` und `/run/media` weiterhin hart blockiert (`STORAGE-PROTECTION-005`),
  - keine `validate_write_target`-Nutzung.
- Blockierende Schritte sind begrenzt:
  - Validierung in `asyncio.to_thread(...)` + `asyncio.wait_for(..., timeout=3s)`,
  - Dateiscan in `asyncio.to_thread(...)` + `asyncio.wait_for(..., timeout=4s)`.
- Dateiscan ist nicht rekursiv und filtert nur Backup-Endungen (`.tar.gz`, `.tar.gz.gpg`, `.tar.gz.enc`).
- Timeout-Rückgabe ist strukturiert (`backup.list_timeout`) mit Details (`command`, `timeout_seconds`, `target`).

### `GET /api/backup/list` Decouple über Backup-Index (FIX-11)

- Der Requestpfad von `backup/list` führt **keine Directory-Enumeration** mehr aus (kein `glob`/`scandir` auf dem Ziel-Mount).
- Neue Primärquelle ist ein lokaler Index: `backup-index.json` unter `SETUPHELFER_STATE_DIR` (Fallback: `/var/lib/setuphelfer`).
- Bei erfolgreichem Backup wird ein Indexeintrag geschrieben/aktualisiert mit:
  - `backup_file`, `created_at`, `encrypted`, `size_bytes`, `type`, `target`, `source_summary`, `manifest_present`, `verification_status`, `storage_path`.
- Sicherheitsregel bleibt unverändert:
  - `/media` und `/run/media` werden sofort mit `backup.path_invalid` + `STORAGE-PROTECTION-005` blockiert.
- Wenn kein Index vorhanden ist, antwortet der Endpoint deterministisch und nicht blockierend mit leerer Liste (`index_available=false`).
- Optionaler Dateiexistenz-Check läuft nur als kurzer `quick_stat`; bei Timeout bleibt der Eintrag sichtbar mit `status=unknown`.

### `POST /api/backup/restore` Enforcement (FIX-12)

- API-Vertrag ist jetzt strikt:
  - `mode=preview`: nur Analyse + Preview-Extraktion in Sandbox, **keine** produktive Zielschreiboperation.
  - `mode=restore`: echter Restore-Pfad; `target_dir` ist Pflicht.
- Harte Restore-Zielvalidierung bei `mode=restore`:
  - fehlendes `target_dir` -> `backup.restore_target_missing`
  - ungültiges Ziel (`/`, Storage-Schutz, kritische Pfade) -> `backup.restore_target_invalid`
  - nicht beschreibbares Ziel -> `backup.restore_not_writable`
- Preview und Restore laufen über getrennte Codepfade; Restore geht nicht mehr durch den Preview-Handler.
- Erfolgs-Codes:
  - Preview -> `backup.restore_preview_ok`
  - Restore -> `backup.restore_success`
- Archivsicherheit bleibt erhalten:
  - Traversal/absolute/unsichere Einträge -> `backup.restore_blocked_entries` (`RESTORE-PATH-004`).

### Restore-Sicherheitsmodell (FIX-12)

- Kein Restore nach `/` (harter Block: `backup.restore_target_invalid`, `RESTORE-RUNTIME-006`).
- Kein Restore nach `/media` oder `/run/media` (harter Block: `backup.restore_target_invalid`, typ. `STORAGE-PROTECTION-005`).
- Kein Restore ohne Schreibrechte auf Zielpfad (`backup.restore_not_writable`, typ. `PERM-GROUP-008`).
- Kein Restore ohne `target_dir` bei `mode=restore` (`backup.restore_target_missing`).

### API-Code -> Diagnose-ID (Restore, FIX-12)

| API-`code` | Typische `details.diagnosis_id` |
|------------|----------------------------------|
| `backup.restore_target_missing` | `RESTORE-RUNTIME-006` |
| `backup.restore_target_invalid` | z. B. `STORAGE-PROTECTION-005` / `RESTORE-RUNTIME-006` |
| `backup.restore_not_writable` | `PERM-GROUP-008` |
| `backup.restore_success` | – |

## Restore-Test (isoliert)

Ziel: Datei-Restore **ohne** Schreiben nach `/` oder produktiven Systempfaden – nur unter `/tmp/setuphelfer-restore-test`.

**API:** `restore_files(archive_path, target_directory, allowed_target_prefixes=(Path("/tmp/setuphelfer-restore-test"),), dry_run=False)` aus `backend/modules/restore_engine.py`. `target_directory` muss unter mindestens einem Eintrag von `allowed_target_prefixes` liegen (`path_under_any_prefix`); das ist die Allowlist-Prüfung und darf nicht umgangen werden.

**Skript:** `tools/setuphelfer_restore_isolated_test.py` – leert und legt das Zielverzeichnis an, ruft `restore_files` auf und prüft Struktur, Beispieldateien, Symlinks (`readlink`) sowie, dass alle **Pfadknoten** unter der Restore-Wurzel liegen (ohne Symlink-Ziele aufzulösen).

**Aufruf (Repo-Root):**

```bash
PYTHONPATH=backend python3 tools/setuphelfer_restore_isolated_test.py
# oder eigenes Archiv:
SETUPHELFER_RESTORE_TEST_ARCHIVE=/pfad/zum/backup.tar.gz PYTHONPATH=backend python3 tools/setuphelfer_restore_isolated_test.py
```

**Ergebnis (Stand Prüfung im Repo):** Lauf ohne Archivargument erzeugt ein synthetisches `etc/`-Abbild per `create_file_backup` (im Skript wird dafür die Ziel-Mount-Validierung der Engine bewusst umgangen, weil `/tmp` kein externes Backup-Medium ist) und stellt nach isoliertem Restore die erwarteten Symlinks (u. a. `50-pipewire.conf` → `/usr/share/alsa/alsa.conf.d/50-pipewire.conf`) wieder her; JSON-Bericht unter `/tmp/setuphelfer-restore-test-report.json`. Ein produktionnahes VM-Archiv muss über Variable/Argument angebunden werden, damit exakt dieselben Dateipfade wie auf der Quell-VM geprüft werden können.

**Grenzen:** Kein Boot-Nachweis; absolute Symlink-Ziele zeigen beim `readlink` aus dem Restore-Baum heraus – das ist beabsichtigt kompatibel zu Debian-`/etc`, stellt aber keine „Inhalt liegt unter Restore-Wurzel“-Garantie dar.

## Deterministisches Restore-Verhalten (Release 1.5)

- **Keine manuellen Post-Fixes in der Produktpipeline:** Ein erfolgreicher Datei-Backup-Lauf endet nur mit einem Archiv, in dem **`MANIFEST.json`** nachweisbar eingebettet ist; andernfalls wird das Artefakt verworfen (**Fail-Fast**, siehe [BACKUP_MANIFEST.md](./BACKUP_MANIFEST.md)).
- **Restore/Verify-Engines** liefern strukturierte Ergebnisse (`message_key` / Details), ohne „Erfolg mit Warnung“ für kritische Integritätsfehler auf den beschriebenen API-Pfaden.
- **systemd-Finalzustand nach Installation:** `scripts/install-system.sh` richtet `setuphelfer-backend` und `setuphelfer` (Web-UI) ein, führt `daemon-reload` aus und prüft, dass beide Units **aktiv** sind. Anpassungen an Speicherlimits und Capabilities für die UI-Unit sind im Installer/Debian-Service hinterlegt (siehe `setuphelfer.service` im Repo).
- **English (short):** Deterministic restore means mandatory manifest embedding, fail-fast on corrupt or incomplete archives, and the installer leaves both systemd services in an active, supported configuration—no ad-hoc manual service edits should be required after a standard install.

## Nicht bewiesene Full-Recovery-Aspekte

- Kein realer Reboot-/Bootloader-Nachweis durch die Unit-Tests allein.
- Ein **VM-orientierter** Boot-Nachweis nach Restore ist in der Wissensbasis unter [FULL_RESTORE_BOOT_TEST.md](../knowledge-base/FULL_RESTORE_BOOT_TEST.md) beschrieben (ergänzend zu den isolierten Restore-Tests).
- Kein Nachweis auf echter Raspberry-Pi-Hardware in dieser Dokumentationsrunde.

## Siehe auch

- Nutzerüberblick: In-App **Dokumentation** → Kapitel **Backup & Restore** und **FAQ**.
- Bestehende UI-/API-Logik: `backend/modules/backup.py`, `app.py` (Backup-Jobs).
- Geplanter Ausbau **echte Home-Daten** (nur explizit, nach HW- und Freigabe-Gates): [TODO_REAL_DATA_HOME_BACKUP.md](./TODO_REAL_DATA_HOME_BACKUP.md).
