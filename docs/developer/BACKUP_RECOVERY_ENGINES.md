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
- **`ReadWritePaths`** enthält weiterhin `/mnt` (und ggf. andere Mount-Basen), damit eingehängte Ziele erreichbar sind.

**Prüfung vor dem Backup:** Nach der Mount-/Dateisystem-Validierung führt `validate_backup_target` einen **echten Schreibtest** im Archiv-Elternverzeichnis aus (kurzlebige Probedatei). Schlägt dieser fehl, bricht die Engine mit dem stabilen Schlüssel `backup_recovery.error.backup_target_not_writable` ab — **ohne** automatisches `chown`/`chmod` im Normalbetrieb.

**Optional (nur kontrollierte Test-VMs):** Wenn die Umgebungsvariable **`SETUPHELFER_FIX_PERMISSIONS=1`** gesetzt ist, versucht das Backend **einmalig** vor der Validierung (mit `sudo`), das gewählte Backup-Verzeichnis auf `root:<SETUPHELFER_BACKUP_GROUP oder setuphelfer>` und `0770` zu setzen, und protokolliert das deutlich im Log. Standardmäßig ist das deaktiviert.

**FAQ: Warum funktioniert mein Backup nicht ohne sudo?** Wenn das Ziel **`root:root`** mit **`0755`** gemountet ist, kann ein normaler Nutzer dort nicht schreiben — früher half oft manuelles `chown`. Mit dem Gruppenmodell reicht es, den Mount-Punkt **einmalig** als Administrator auf **`root:setuphelfer`** und **`0770`** zu setzen (oder das VM-Helferskript `in-guest-prepare-backup-disk.sh` mit `VMTEST_BACKUP_OWNER_GROUP=setuphelfer` zu nutzen). Der Dienst braucht dann kein dauerhaftes „alles als root schreiben“ und kein `777`.

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
