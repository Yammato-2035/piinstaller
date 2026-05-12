"""
i18n-Schlüssel für Backup/Recovery – keine UI-Strings in Business-Logik verstreut.
Aufrufer können tr() nutzen; Standardtexte nur in DEFAULT_CATALOG (ersetzbar durch gettext).
"""

from __future__ import annotations

import os
from typing import Any, Mapping

# Nur stabile Schlüssel; Werte optional in DEFAULT_CATALOG
K_DEVICE_NOT_ALLOWED = "backup_recovery.error.device_not_allowed"
K_PATH_NOT_ALLOWED = "backup_recovery.error.path_not_allowed"
K_OUTPUT_NOT_ALLOWED = "backup_recovery.error.output_not_allowed"
K_DD_FAILED = "backup_recovery.error.dd_failed"
K_TAR_FAILED = "backup_recovery.error.tar_failed"
K_MANIFEST_WRITE_FAILED = "backup_recovery.error.manifest_write_failed"
K_SFDISK_FAILED = "backup_recovery.error.sfdisk_failed"
K_MISSING_MANIFEST = "backup_recovery.error.missing_manifest"
K_BACKUP_FAILED_MANIFEST_MISSING = "backup_recovery.error.backup_failed_manifest_missing"
K_ARCHIVE_CORRUPT = "backup_recovery.error.archive_corrupt"
K_VERIFY_INTEGRITY_FAILED = "backup_recovery.error.verify_integrity_failed"
K_CHECKSUM_MISMATCH = "backup_recovery.error.checksum_mismatch"
K_EXTRACT_FAILED = "backup_recovery.error.extract_failed"
K_MOUNT_FAILED = "backup_recovery.error.mount_failed"
K_LOOP_FAILED = "backup_recovery.error.loop_setup_failed"
K_RESTORE_PT_FAILED = "backup_recovery.error.restore_partition_table_failed"
K_RESTORE_IMAGE_FAILED = "backup_recovery.error.restore_image_failed"
K_RESTORE_FILES_FAILED = "backup_recovery.error.restore_files_failed"
K_BOOTLOADER_FAILED = "backup_recovery.error.bootloader_failed"
K_CRYPTO_KEY_MISSING = "backup_recovery.error.crypto_key_missing"
K_CRYPTO_FAILED = "backup_recovery.error.crypto_failed"
K_USB_MOUNT_FAILED = "backup_recovery.error.usb_mount_failed"
K_WEBDAV_FAILED = "backup_recovery.error.webdav_failed"
K_DOWNLOAD_FAILED = "backup_recovery.error.download_failed"
K_BACKUP_TARGET_PARENT_MISSING = "backup_recovery.error.backup_target_parent_missing"
K_BACKUP_TARGET_NOT_MOUNTED = "backup_recovery.error.backup_target_not_mounted"
K_BACKUP_TARGET_ROOT_FILESYSTEM = "backup_recovery.error.backup_target_root_filesystem"
K_BACKUP_TARGET_NON_BLOCK_SOURCE = "backup_recovery.error.backup_target_non_block_source"
K_BACKUP_TARGET_LIVE_FILESYSTEM = "backup_recovery.error.backup_target_live_filesystem"
K_BACKUP_TARGET_FILESYSTEM_NOT_PERMITTED = "backup_recovery.error.backup_target_filesystem_not_permitted"
K_BACKUP_TARGET_NOT_WRITABLE = "backup_recovery.error.backup_target_not_writable"
K_BACKUP_TARGET_WRITE_PROTECTED = "backup_recovery.error.backup_target_write_protected"

# recovery/main.py
K_RECOVERY_MENU_TITLE = "recovery.menu.title"
K_RECOVERY_OPT_USB = "recovery.menu.option_usb"
K_RECOVERY_OPT_CLOUD = "recovery.menu.option_cloud"
K_RECOVERY_OPT_DIAG = "recovery.menu.option_diagnose"
K_RECOVERY_ROOT_MISSING = "recovery.status.root_unhealthy"
K_OPERATION_OK = "backup_recovery.ok"

def _locale_prefers_german() -> bool:
    for var in ("SETUPHELFER_LANG", "LC_MESSAGES", "LANG"):
        v = (os.environ.get(var) or "").strip().lower()
        if v.startswith("de"):
            return True
    return False


DEFAULT_CATALOG: dict[str, str] = {
    K_DEVICE_NOT_ALLOWED: "Block device is not on the allowlist.",
    K_PATH_NOT_ALLOWED: "Path is not under an allowed backup prefix.",
    K_OUTPUT_NOT_ALLOWED: "Output path is not under an allowed output prefix.",
    K_DD_FAILED: "Creating raw image failed.",
    K_TAR_FAILED: "Creating file archive failed.",
    K_MANIFEST_WRITE_FAILED: "Writing manifest failed.",
    K_SFDISK_FAILED: "Reading partition layout failed.",
    K_MISSING_MANIFEST: "Manifest missing or invalid.",
    K_BACKUP_FAILED_MANIFEST_MISSING: "Backup failed: MANIFEST.json is missing or could not be embedded; the archive was discarded.",
    K_ARCHIVE_CORRUPT: "Archive gzip layer is corrupt or truncated.",
    K_VERIFY_INTEGRITY_FAILED: "Deep verification found integrity errors (see errors list).",
    K_CHECKSUM_MISMATCH: "Checksum verification failed.",
    K_EXTRACT_FAILED: "Archive extraction failed.",
    K_MOUNT_FAILED: "Read-only mount failed.",
    K_LOOP_FAILED: "Loop device setup failed.",
    K_RESTORE_PT_FAILED: "Restoring partition table failed.",
    K_RESTORE_IMAGE_FAILED: "Restoring disk image failed.",
    K_RESTORE_FILES_FAILED: "Restoring files failed.",
    K_BOOTLOADER_FAILED: "Bootloader installation failed.",
    K_CRYPTO_KEY_MISSING: "Encryption key not provided.",
    K_CRYPTO_FAILED: "Encryption or decryption failed.",
    K_USB_MOUNT_FAILED: "USB auto-mount failed.",
    K_WEBDAV_FAILED: "WebDAV connection failed.",
    K_DOWNLOAD_FAILED: "Backup download failed.",
    K_BACKUP_TARGET_PARENT_MISSING: "Backup target directory does not exist or is not a directory.",
    K_BACKUP_TARGET_NOT_MOUNTED: "Backup target is not on a mounted filesystem.",
    K_BACKUP_TARGET_ROOT_FILESYSTEM: "Backups on the root filesystem (/) are not allowed.",
    K_BACKUP_TARGET_NON_BLOCK_SOURCE: "Backup target is not backed by a local block device.",
    K_BACKUP_TARGET_LIVE_FILESYSTEM: "Backup target uses a live/read-only medium filesystem.",
    K_BACKUP_TARGET_FILESYSTEM_NOT_PERMITTED: "Backup target filesystem is not permitted for backups.",
    K_BACKUP_TARGET_NOT_WRITABLE: "Backup target directory is not writable for the Setuphelfer process (check owner/group, e.g. root:setuphelfer and mode 0770).",
    K_BACKUP_TARGET_WRITE_PROTECTED: "Backup or restore target blocked by storage write protection (see diagnosis id in details).",
    K_RECOVERY_MENU_TITLE: "Setuphelfer recovery",
    K_RECOVERY_OPT_USB: "Restore from USB",
    K_RECOVERY_OPT_CLOUD: "Restore from cloud",
    K_RECOVERY_OPT_DIAG: "Diagnostics",
    K_RECOVERY_ROOT_MISSING: "Root system appears incomplete; recovery mode.",
    K_OPERATION_OK: "OK",
}

DEFAULT_CATALOG_DE: dict[str, str] = {
    K_DEVICE_NOT_ALLOWED: "Blockgerät steht nicht auf der Allowlist.",
    K_PATH_NOT_ALLOWED: "Pfad liegt nicht unter einem erlaubten Backup-Präfix.",
    K_OUTPUT_NOT_ALLOWED: "Ausgabepfad liegt nicht unter einem erlaubten Ausgabe-Präfix.",
    K_DD_FAILED: "Erzeugen des Rohabbilds ist fehlgeschlagen.",
    K_TAR_FAILED: "Erzeugen des Dateiarchivs ist fehlgeschlagen.",
    K_MANIFEST_WRITE_FAILED: "Schreiben des Manifests ist fehlgeschlagen.",
    K_SFDISK_FAILED: "Lesen der Partitionstabelle (sfdisk) ist fehlgeschlagen.",
    K_MISSING_MANIFEST: "Manifest fehlt oder ist ungültig.",
    K_BACKUP_FAILED_MANIFEST_MISSING: "Backup fehlgeschlagen: MANIFEST.json fehlt oder konnte nicht eingebettet werden; das Archiv wurde verworfen.",
    K_ARCHIVE_CORRUPT: "Gzip-Schicht des Archivs ist beschädigt oder abgeschnitten.",
    K_VERIFY_INTEGRITY_FAILED: "Tiefenprüfung hat Integritätsfehler gefunden (siehe Fehlerliste).",
    K_CHECKSUM_MISMATCH: "Prüfsummenvergleich ist fehlgeschlagen.",
    K_EXTRACT_FAILED: "Entpacken des Archivs ist fehlgeschlagen.",
    K_MOUNT_FAILED: "Read-only-Einhängen ist fehlgeschlagen.",
    K_LOOP_FAILED: "Einrichten des Loop-Devices ist fehlgeschlagen.",
    K_RESTORE_PT_FAILED: "Wiederherstellen der Partitionstabelle ist fehlgeschlagen.",
    K_RESTORE_IMAGE_FAILED: "Wiederherstellen des Datenträgerabbilds ist fehlgeschlagen.",
    K_RESTORE_FILES_FAILED: "Wiederherstellen der Dateien ist fehlgeschlagen.",
    K_BOOTLOADER_FAILED: "Installation des Bootloaders ist fehlgeschlagen.",
    K_CRYPTO_KEY_MISSING: "Verschlüsselungsschlüssel fehlt.",
    K_CRYPTO_FAILED: "Verschlüsselung oder Entschlüsselung ist fehlgeschlagen.",
    K_USB_MOUNT_FAILED: "Automatisches Einhängen von USB ist fehlgeschlagen.",
    K_WEBDAV_FAILED: "WebDAV-Verbindung ist fehlgeschlagen.",
    K_DOWNLOAD_FAILED: "Backup-Download ist fehlgeschlagen.",
    K_BACKUP_TARGET_PARENT_MISSING: "Backup-Zielverzeichnis existiert nicht oder ist kein Verzeichnis.",
    K_BACKUP_TARGET_NOT_MOUNTED: "Backup-Ziel liegt nicht auf einem gemounteten Dateisystem.",
    K_BACKUP_TARGET_ROOT_FILESYSTEM: "Backups auf dem Root-Dateisystem (/) sind nicht erlaubt.",
    K_BACKUP_TARGET_NON_BLOCK_SOURCE: "Backup-Ziel hängt nicht an einem lokalen Blockgerät (z. B. tmpfs oder Netzwerk-FS).",
    K_BACKUP_TARGET_LIVE_FILESYSTEM: "Backup-Ziel nutzt ein Live-/schreibgeschütztes Dateisystem.",
    K_BACKUP_TARGET_FILESYSTEM_NOT_PERMITTED: "Dateisystem am Backup-Ziel ist für Backups nicht zugelassen.",
    K_BACKUP_TARGET_NOT_WRITABLE: "Backup-Ziel ist für den Setuphelfer-Prozess nicht beschreibbar (Besitzer/Gruppe prüfen, z. B. root:setuphelfer und Modus 0770).",
    K_BACKUP_TARGET_WRITE_PROTECTED: "Backup- oder Restore-Ziel durch Storage-Schreibschutz blockiert (Diagnose-ID in den Details).",
    K_RECOVERY_MENU_TITLE: "Setuphelfer-Wiederherstellung",
    K_RECOVERY_OPT_USB: "Wiederherstellen von USB",
    K_RECOVERY_OPT_CLOUD: "Wiederherstellen aus der Cloud",
    K_RECOVERY_OPT_DIAG: "Diagnose",
    K_RECOVERY_ROOT_MISSING: "Root-System wirkt unvollständig; Wiederherstellungsmodus.",
    K_OPERATION_OK: "OK",
}


def tr(key: str, catalog: Mapping[str, str] | None = None, **kwargs: Any) -> str:
    """Übersetzter Text oder Schlüssel; kwargs für einfache {name}-Platzhalter."""
    base = dict(DEFAULT_CATALOG)
    if _locale_prefers_german():
        base.update(DEFAULT_CATALOG_DE)
    if catalog is not None:
        base.update(dict(catalog))
    c = base
    template = c.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
