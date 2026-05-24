"""
Manifest-Layout-Vorschau aus Backup-Manifest (Phase 2, read-only).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

ManifestStatus = str  # ok | review_required | unavailable | blocked


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry_from_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "device": row.get("device") or row.get("path"),
        "size": row.get("size"),
        "fs_type": row.get("fs_type") or row.get("fstype"),
        "mountpoint": row.get("mountpoint"),
        "label": row.get("label"),
        "uuid": row.get("uuid"),
        "flags": row.get("flags") if isinstance(row.get("flags"), list) else [],
        "boot_hint": row.get("boot") or row.get("boot_hint"),
        "efi_hint": row.get("efi") or row.get("efi_hint"),
        "source": "manifest_entry",
    }


def _parse_sfdisk_lines(layout: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in layout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "label: gpt":
            continue
        if stripped.endswith(":") and " " in stripped:
            parts = stripped.rstrip(":").split()
            out.append(
                {
                    "device": parts[0] if parts else stripped,
                    "size": parts[1] if len(parts) > 1 else None,
                    "type": parts[-1] if len(parts) > 2 else None,
                    "source": "partition_layout_sfdisk_d",
                }
            )
            continue
        if stripped.startswith(","):
            cols = [c.strip() for c in stripped.lstrip(",").split(",")]
            out.append(
                {
                    "device": None,
                    "size": cols[0] if cols else None,
                    "fs_type": cols[2] if len(cols) > 2 else None,
                    "label": cols[3] if len(cols) > 3 else None,
                    "flags": [cols[4]] if len(cols) > 4 and cols[4] else [],
                    "source": "partition_layout_sfdisk_d",
                }
            )
    return out


def _extract_partitions_list(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    parts = manifest.get("partitions")
    if isinstance(parts, list) and parts:
        return [_entry_from_manifest_row(p) for p in parts if isinstance(p, dict)]
    layout_obj = manifest.get("layout")
    if isinstance(layout_obj, dict):
        pl = layout_obj.get("partitions")
        if isinstance(pl, list):
            return [_entry_from_manifest_row(p) for p in pl if isinstance(p, dict)]
    return []


def _build_layout_struct(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    system = manifest.get("system") if isinstance(manifest.get("system"), dict) else {}
    mountpoints = [
        r.get("mountpoint")
        for r in rows
        if isinstance(r, dict) and r.get("mountpoint")
    ]
    boot_rows = [r for r in rows if r.get("boot_hint") or r.get("mountpoint") in ("/boot", "/boot/efi")]
    efi_rows = [
        r
        for r in rows
        if r.get("efi_hint")
        or str(r.get("fs_type") or "").lower() in ("vfat", "fat32", "efi")
        or str(r.get("mountpoint") or "").endswith("efi")
    ]
    return {
        "source_system": system,
        "filesystems": [
            {
                "device": r.get("device"),
                "fs_type": r.get("fs_type"),
                "size": r.get("size"),
                "uuid": r.get("uuid"),
            }
            for r in rows
            if isinstance(r, dict)
        ],
        "mountpoints": mountpoints,
        "boot": boot_rows[0] if boot_rows else {},
        "efi": efi_rows[0] if efi_rows else {},
    }


def _compatibility(
    target_device: str | None, manifest: dict[str, Any], rows: list[dict[str, Any]]
) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    layout_text = manifest.get("partition_layout_sfdisk_d")
    if not rows and not (isinstance(layout_text, str) and layout_text.strip()):
        warnings.append(
            {
                "code": "partition.manifest.layout_missing",
                "message": "Kein erkennbares Partition-Layout im Manifest.",
            }
        )
    boot = any(r.get("boot_hint") for r in rows if isinstance(r, dict))
    efi = any(
        r.get("efi_hint")
        or str(r.get("mountpoint") or "").endswith("efi")
        for r in rows
        if isinstance(r, dict)
    )
    if rows and not boot and not efi:
        warnings.append(
            {
                "code": "partition.manifest.boot_efi_missing",
                "message": "Boot-/EFI-Hinweise fehlen – Restore-Kompatibilität manuell prüfen.",
            }
        )
    return {
        "target_device": (target_device or "").strip() or None,
        "warnings": warnings,
        "errors": errors,
    }


def build_manifest_layout_preview(
    manifest: dict[str, Any] | None,
    target_device: str | None = None,
    *,
    manifest_path: str | None = None,
    manifest_reader: Callable[[str | None], tuple[dict[str, Any] | None, str | None]] | None = None,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "source": "backup_manifest",
        "target_device": (target_device or "").strip() or None,
        "write_allowed": False,
        "generated_at": _utc_now(),
        "manifest_source": "inline" if manifest else "null",
        "manifest_path": None,
    }

    effective_manifest = manifest if isinstance(manifest, dict) else None
    read_err: str | None = None

    if manifest_path and str(manifest_path).strip():
        base["manifest_path"] = str(manifest_path).strip()
        if manifest_reader is not None:
            loaded, read_err = manifest_reader(manifest_path)
            if loaded is not None:
                effective_manifest = loaded
                base["manifest_source"] = "file_readonly"
            elif effective_manifest is None:
                base["manifest_source"] = "file_readonly"
        elif effective_manifest is None:
            base["manifest_source"] = "file_readonly"
            read_err = "manifest_reader_unavailable"

    if read_err and effective_manifest is None:
        blocked = read_err in ("path_traversal", "path_not_allowlisted", "invalid_json")
        return {
            **base,
            "status": "blocked" if blocked else "review_required",
            "original_layout": [],
            "suggested_layout": [],
            "layout": {
                "source_system": {},
                "filesystems": [],
                "mountpoints": [],
                "boot": {},
                "efi": {},
            },
            "compatibility": {
                "target_device": base["target_device"],
                "warnings": [],
                "errors": [
                    {
                        "code": f"partition.manifest.read_{read_err}",
                        "message": f"Manifest konnte nicht gelesen werden ({read_err}).",
                    }
                ],
            },
            "warnings": [
                {
                    "code": f"partition.manifest.read_{read_err}",
                    "message": f"Manifest-Lesen fehlgeschlagen: {read_err}.",
                }
            ],
        }

    if not effective_manifest or not isinstance(effective_manifest, dict):
        return {
            **base,
            "status": "unavailable",
            "original_layout": [],
            "suggested_layout": [],
            "layout": {
                "source_system": {},
                "filesystems": [],
                "mountpoints": [],
                "boot": {},
                "efi": {},
            },
            "compatibility": {
                "target_device": base["target_device"],
                "warnings": [],
                "errors": [],
            },
            "warnings": [
                {
                    "code": "partition.manifest.missing",
                    "message": "Kein Backup-Manifest übergeben.",
                }
            ],
        }

    kind = str(effective_manifest.get("kind") or "")
    if kind and "manifest" not in kind.lower() and "backup" not in kind.lower():
        return {
            **base,
            "status": "review_required",
            "original_layout": [],
            "suggested_layout": [],
            "layout": _build_layout_struct(effective_manifest, []),
            "compatibility": {
                "target_device": base["target_device"],
                "warnings": [
                    {
                        "code": "partition.manifest.unknown_kind",
                        "message": f"Unbekannter Manifest-Typ: {kind}",
                    }
                ],
                "errors": [],
            },
            "warnings": [
                {
                    "code": "partition.manifest.unknown_kind",
                    "message": f"Manifest-kind nicht erkannt: {kind}",
                }
            ],
        }

    original: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    original.extend(_extract_partitions_list(effective_manifest))

    layout_text = effective_manifest.get("partition_layout_sfdisk_d")
    if isinstance(layout_text, str) and layout_text.strip():
        original.extend(_parse_sfdisk_lines(layout_text))

    entries = effective_manifest.get("entries")
    if isinstance(entries, list):
        for e in entries:
            if isinstance(e, dict) and e.get("type") == "partition":
                original.append(_entry_from_manifest_row(e))

    layout_struct = _build_layout_struct(effective_manifest, original)
    compatibility = _compatibility(target_device, effective_manifest, original)

    if not original:
        return {
            **base,
            "status": "review_required",
            "original_layout": [],
            "suggested_layout": [],
            "layout": layout_struct,
            "compatibility": compatibility,
            "warnings": compatibility.get("warnings") or [
                {
                    "code": "partition.manifest.layout_missing",
                    "message": "Manifest ohne erkennbares Partition-Layout.",
                }
            ],
        }

    suggested = [dict(row) for row in original]
    if target_device:
        warnings.append(
            {
                "code": "partition.manifest.preview_only",
                "message": f"Vorschlag für Ziel {target_device} – keine Anwendung in Phase 2.",
            }
        )
    warnings.extend(compatibility.get("warnings") or [])

    status = "ok"
    if compatibility.get("warnings"):
        status = "review_required"

    return {
        **base,
        "status": status,
        "original_layout": original,
        "suggested_layout": suggested,
        "layout": layout_struct,
        "compatibility": compatibility,
        "warnings": warnings,
    }
