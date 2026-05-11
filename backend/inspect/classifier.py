"""
Inspect Phase 2 – Klassifikation nur aus vorhandenen Inspect-Rohdaten (keine neue Erkennung).
Defensiv: im Zweifel UNKNOWN / PARTIAL_SYSTEM; NTFS allein ≠ sicheres Windows.
"""

from __future__ import annotations

from typing import Any

# Boot-Codes wie in collector._collect_os_hints / inspect_boot (nur Auswertung vorhandener Liste)
_BAD_BOOT_CODES: frozenset[str] = frozenset(
    {
        "rescue.boot.kernel_missing",
        "rescue.boot.boot_dir_missing",
        "rescue.boot.fstab_missing",
        "rescue.boot.fstab_unreadable",
        "rescue.boot.fstab_parse_error",
        "rescue.boot.initrd_missing",
    }
)

_LINUX_FS = frozenset({"ext2", "ext3", "ext4", "xfs", "btrfs"})
_EFI_LIKE = frozenset({"vfat", "fat32"})


def _filesystem_types(detected: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(detected, dict):
        return out
    for meta in detected.values():
        if isinstance(meta, dict):
            t = meta.get("type")
            if isinstance(t, str) and t.strip():
                out.add(t.strip().lower())
    return out


def _ntfs_partition_count(detected: Any) -> int:
    if not isinstance(detected, dict):
        return 0
    n = 0
    for meta in detected.values():
        if isinstance(meta, dict) and str(meta.get("type", "")).strip().lower() == "ntfs":
            n += 1
    return n


def _partition_count(devices_raw: Any) -> int:
    n = 0
    if not isinstance(devices_raw, list):
        return 0
    for node in devices_raw:
        if not isinstance(node, dict):
            continue
        parts = node.get("partitions")
        if isinstance(parts, list):
            n += len(parts)
    return n


def _os_hints(inspect_result: dict[str, Any]) -> dict[str, Any]:
    cap = inspect_result.get("capabilities")
    if not isinstance(cap, dict):
        return {}
    h = cap.get("os_hints")
    return h if isinstance(h, dict) else {}


def _strong_windows_evidence(
    *,
    types_set: set[str],
    detected: Any,
) -> bool:
    """
    NTFS allein reicht nicht: Zusatzsignal nur aus Phase-0/1 (`detect_filesystems`-Map):
    EFI-ähnlicher Typ (vfat/fat32) zusätzlich zu NTFS, oder mindestens zwei NTFS-Partitionen.
    Kein Microsoft-Dateiscan (Payload liefert keine Pfade unter /boot/efi).
    """
    if "ntfs" not in types_set:
        return False
    if types_set & _EFI_LIKE:
        return True
    if _ntfs_partition_count(detected) >= 2:
        return True
    return False


def classify_system(inspect_result: dict[str, Any]) -> dict[str, Any]:
    """
    Liefert system_type, confidence, indicators (Codes), risk_level.
    Nutzt ausschließlich Felder aus inspect_result (Phase-0/1-Form).
    """
    indicators: list[str] = []
    hints = _os_hints(inspect_result)
    boot = inspect_result.get("boot")
    boot = boot if isinstance(boot, dict) else {}
    codes_raw = boot.get("codes")
    codes: list[str] = [c for c in codes_raw if isinstance(c, str)] if isinstance(codes_raw, list) else []

    fs = inspect_result.get("filesystems")
    fs = fs if isinstance(fs, dict) else {}
    detected = fs.get("detected")
    types_set = _filesystem_types(detected)

    storage = inspect_result.get("storage")
    storage = storage if isinstance(storage, dict) else {}
    devices_raw = storage.get("devices_raw")
    part_n = _partition_count(devices_raw)

    has_ntfs = "ntfs" in types_set
    has_linux_fs = bool(types_set & _LINUX_FS)

    esp = boot.get("esp")
    esp_present = isinstance(esp, dict) and esp.get("present") is True

    fstab_ok = boot.get("fstab_parse_ok") is True and boot.get("fstab_exists") is True
    kernel_files = boot.get("kernel_files")
    has_kernels = isinstance(kernel_files, list) and len(kernel_files) > 0

    broken_boot = bool(hints.get("possible_broken_boot")) or any(c in _BAD_BOOT_CODES for c in codes)
    empty_hint = bool(hints.get("possible_empty_disk"))
    unknown_layout = bool(hints.get("unknown_layout"))

    if has_ntfs:
        indicators.append("classifier.indicator.ntfs_present")
    if has_linux_fs:
        indicators.append("classifier.indicator.linux_fs_present")
    if esp_present:
        indicators.append("classifier.indicator.esp_present")
    if fstab_ok:
        indicators.append("classifier.indicator.fstab_ok")
    if has_kernels:
        indicators.append("classifier.indicator.linux_kernel_artifacts")

    # --- BROKEN_BOOT (höchste Priorität der interpretierbaren Zustände) ---
    if broken_boot:
        indicators.append("classifier.indicator.boot_analysis_issue")
        return {
            "system_type": "BROKEN_BOOT",
            "confidence": 0.82,
            "indicators": indicators,
            "risk_level": "high",
        }

    # --- EMPTY ---
    if empty_hint or (part_n == 0 and not types_set and isinstance(devices_raw, list) and len(devices_raw) > 0):
        indicators.append("classifier.indicator.no_usable_partitions")
        return {
            "system_type": "EMPTY",
            "confidence": 0.75 if empty_hint else 0.55,
            "indicators": indicators,
            "risk_level": "low",
        }

    # --- DUALBOOT (NTFS + Linux-FS laut detect_filesystems), defensive confidence ---
    if has_ntfs and has_linux_fs:
        indicators.append("classifier.indicator.dualboot_filesystem_pattern")
        conf = 0.72
        if unknown_layout:
            conf = 0.58
            indicators.append("classifier.indicator.dualboot_uncertain_layout")
        if not bool(hints.get("possible_dualboot")):
            conf = max(0.52, conf - 0.1)
            indicators.append("classifier.indicator.dualboot_hint_mismatch")
        return {
            "system_type": "DUALBOOT",
            "confidence": round(min(1.0, conf), 3),
            "indicators": indicators,
            "risk_level": "high" if conf >= 0.65 else "medium",
        }

    # --- LINUX ---
    if has_linux_fs and not has_ntfs:
        conf = 0.88
        if unknown_layout:
            conf = max(0.4, conf - 0.2)
            indicators.append("classifier.indicator.conflicting_unknown_layout")
        if not fstab_ok:
            conf -= 0.1
            indicators.append("classifier.indicator.fstab_incomplete")
        return {
            "system_type": "LINUX",
            "confidence": round(min(1.0, conf), 3),
            "indicators": indicators,
            "risk_level": "low" if conf >= 0.75 else "medium",
        }

    # --- NTFS ohne Linux-FS: WINDOWS nur mit starkem Zusatzsignal, sonst PARTIAL_SYSTEM ---
    if has_ntfs and not has_linux_fs:
        strong = _strong_windows_evidence(types_set=types_set, detected=detected)
        if strong:
            indicators.append("classifier.indicator.windows_layout_pattern")
            conf = 0.62
            if types_set & _EFI_LIKE:
                conf = min(0.72, conf + 0.08)
            if _ntfs_partition_count(detected) >= 2:
                conf = min(0.74, conf + 0.06)
            if unknown_layout:
                conf = max(0.45, conf - 0.15)
                indicators.append("classifier.indicator.conflicting_unknown_layout")
            return {
                "system_type": "WINDOWS",
                "confidence": round(min(0.76, conf), 3),
                "indicators": indicators,
                "risk_level": "medium",
            }
        indicators.append("classifier.indicator.ntfs_only_ambiguous")
        return {
            "system_type": "PARTIAL_SYSTEM",
            "confidence": 0.44,
            "indicators": indicators,
            "risk_level": "medium",
        }

    # --- PARTIAL_SYSTEM: Fragmente ohne klares Muster ---
    if part_n > 0 and (not types_set or unknown_layout):
        indicators.append("classifier.indicator.partial_or_unclassified_layout")
        return {
            "system_type": "PARTIAL_SYSTEM",
            "confidence": 0.48,
            "indicators": indicators,
            "risk_level": "medium",
        }

    if bool(hints.get("possible_dualboot")) and not (has_ntfs and has_linux_fs):
        indicators.append("classifier.indicator.dualboot_hint_inconsistent")
        return {
            "system_type": "PARTIAL_SYSTEM",
            "confidence": 0.42,
            "indicators": indicators,
            "risk_level": "medium",
        }

    # --- UNKNOWN ---
    indicators.append("classifier.indicator.insufficient_classification_signal")
    return {
        "system_type": "UNKNOWN",
        "confidence": 0.28,
        "indicators": indicators,
        "risk_level": "medium",
    }
