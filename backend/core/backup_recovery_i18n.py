"""
i18n-Schlüssel für Backup/Recovery – keine UI-Strings in Business-Logik verstreut.
Aufrufer können tr() nutzen; Standardtexte nur in DEFAULT_CATALOG (ersetzbar durch gettext).
"""

from __future__ import annotations

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

# recovery/main.py
K_RECOVERY_MENU_TITLE = "recovery.menu.title"
K_RECOVERY_OPT_USB = "recovery.menu.option_usb"
K_RECOVERY_OPT_CLOUD = "recovery.menu.option_cloud"
K_RECOVERY_OPT_DIAG = "recovery.menu.option_diagnose"
K_RECOVERY_ROOT_MISSING = "recovery.status.root_unhealthy"
K_OPERATION_OK = "backup_recovery.ok"

DEFAULT_CATALOG: dict[str, str] = {
    K_DEVICE_NOT_ALLOWED: "Block device is not on the allowlist.",
    K_PATH_NOT_ALLOWED: "Path is not under an allowed backup prefix.",
    K_OUTPUT_NOT_ALLOWED: "Output path is not under an allowed output prefix.",
    K_DD_FAILED: "Creating raw image failed.",
    K_TAR_FAILED: "Creating file archive failed.",
    K_MANIFEST_WRITE_FAILED: "Writing manifest failed.",
    K_SFDISK_FAILED: "Reading partition layout failed.",
    K_MISSING_MANIFEST: "Manifest missing or invalid.",
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
    K_RECOVERY_MENU_TITLE: "Setuphelfer recovery",
    K_RECOVERY_OPT_USB: "Restore from USB",
    K_RECOVERY_OPT_CLOUD: "Restore from cloud",
    K_RECOVERY_OPT_DIAG: "Diagnostics",
    K_RECOVERY_ROOT_MISSING: "Root system appears incomplete; recovery mode.",
    K_OPERATION_OK: "OK",
}


def tr(key: str, catalog: Mapping[str, str] | None = None, **kwargs: Any) -> str:
    """Übersetzter Text oder Schlüssel; kwargs für einfache {name}-Platzhalter."""
    c = DEFAULT_CATALOG if catalog is None else {**DEFAULT_CATALOG, **dict(catalog)}
    template = c.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
