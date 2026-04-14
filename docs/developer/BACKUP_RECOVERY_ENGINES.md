# Backup- und Recovery-Engines (Worst-Case / Full-Recovery)

Technische Referenz zu den Python-Modulen für Rohabbilder, Dateiarchive, Verifikation, Restore und Recovery-Transport – ergänzend zur UI unter **Backup & Restore**.

## Module (Backend)

| Bereich | Datei | Kurzbeschreibung |
|--------|--------|------------------|
| i18n (Schlüssel) | `backend/core/backup_recovery_i18n.py` | Stabile Meldungsschlüssel und `tr()`; Standardtexte in `DEFAULT_CATALOG` (ersetzbar). |
| Blockgeräte | `backend/core/block_device_allowlist.py` | Nur Whole-Disk-Muster (`/dev/sd[a-z]`, `/dev/nvme…`, `/dev/mmcblkN`). |
| Pfade | `backend/core/backup_path_allowlist.py` | Backup-/Restore-Pfade nur unter konfigurierten Präfixen. |
| Engine | `backend/modules/backup_engine.py` | `create_image_backup`, `create_file_backup`, `create_manifest` (SHA-256, optional `sfdisk -d`, Metadaten). |
| Verifikation | `backend/modules/backup_verify.py` | `verify_basic`, `verify_deep` (Extraktion unter `/tmp/.../setuphelfer_verify/`). |
| Restore | `backend/modules/restore_engine.py` | `restore_partition_table`, `restore_image`, `restore_files`, `install_bootloader` (nur erlaubte Geräte). |
| Transport | `backend/modules/recovery_transport.py` | `auto_mount_usb`, `connect_webdav`, `download_backup` (curl, keine Paketinstallation). |
| Verschlüsselung | `backend/modules/backup_crypto.py` | AES-256-GCM (`cryptography`); **Schlüssel nie im Archiv**. |
| Recovery-CLI | `recovery/main.py` | Menü bei defektem Root-System (USB/WebDAV/Diagnose-Hinweis). |

## Sicherheit und Grenzen

- **Kein** automatisches Installieren von Paketen (z. B. `grub-install` muss vorhanden sein).
- **Destruktive** Befehle (`dd`, `sfdisk`) nur nach expliziter Allowlist-Prüfung.
- **Bootfähigkeit** nach Restore auf echter Hardware ist **manuell** nachzuweisen; automatisierte Tests arbeiten nur in temporären Verzeichnissen (`backend/tests/test_backup_recovery_engines.py`).

## Backup-Modelle (Ist-Stand)

- **Image-basiert:** `create_image_backup` erzeugt ein Rohabbild per `dd` für allowlist-fähige Whole-Disk-Geräte.
- **File-basiert:** `create_file_backup` archiviert Dateien und Verzeichnisse rekursiv als `tar.gz`.
- **Hybrid:** Manifest kann parallel Dateichecksummen und `sfdisk -d`-Layout enthalten, ersetzt aber keinen echten Boot-Nachweis.

## File-Engine (korrigierter Stand)

- Verzeichnisse werden rekursiv gesichert; reguläre Dateien bleiben unterstützt.
- Archivpfade sind relativ zum Root-Kontext (`/etc/hosts -> etc/hosts`), keine flachen `p.name`-Einträge mehr.
- Kollisionsschutz ist aktiv: doppelte Zielpfade im Archiv führen zu sauberem Abbruch.
- Überlappende Eingaben (`/home` plus `/home/user/...`) werden nicht doppelt archiviert; übersprungene Eingaben stehen im Manifest unter `skipped_inputs`.
- Symlinks und Sonderdateien werden restriktiv abgewiesen, damit keine stillen Sicherheits- oder Restore-Überraschungen entstehen.

## Verify/Restore (korrigierter Stand)

- `verify_basic` prüft zusätzlich auf unsichere Archiv-Member (Traversal/absolute Pfade/Link-Sondertypen).
- `verify_deep` validiert Member vor Extraktion und vergleicht Manifest-Pfade gegen die entpackte relative Struktur.
- `restore_files` entpackt nur sichere Member, blockiert Traversal/Links/Sondertypen und schreibt `MANIFEST.json` nicht ins Zielverzeichnis.

## Nicht bewiesene Full-Recovery-Aspekte

- Kein realer Reboot-/Bootloader-Nachweis durch die Unit-Tests.
- Kein Nachweis eines kompletten End-to-End-Laufs (Backup -> Restore -> Boot) in einer frischen VM in diesem Dokument.
- Kein Nachweis auf echter Raspberry-Pi-Hardware in dieser Codeänderung.

## Siehe auch

- Nutzerüberblick: In-App **Dokumentation** → Kapitel **Backup & Restore** und **FAQ**.
- Bestehende UI-/API-Logik: `backend/modules/backup.py`, `app.py` (Backup-Jobs).
