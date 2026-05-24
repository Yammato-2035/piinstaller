"""
Manifest-Layout-Vorschau aus Backup-Manifest (Phase 2, read-only).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ManifestStatus = str  # ok | review_required | unavailable


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


def build_manifest_layout_preview(
    manifest: dict[str, Any] | None,
    target_device: str | None = None,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "source": "backup_manifest",
        "target_device": (target_device or "").strip() or None,
        "write_allowed": False,
        "generated_at": _utc_now(),
    }

    if not manifest or not isinstance(manifest, dict):
        return {
            **base,
            "status": "unavailable",
            "original_layout": [],
            "suggested_layout": [],
            "warnings": [
                {
                    "code": "partition.manifest.missing",
                    "message": "Kein Backup-Manifest übergeben.",
                }
            ],
        }

    original: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    original.extend(_extract_partitions_list(manifest))

    layout_text = manifest.get("partition_layout_sfdisk_d")
    if isinstance(layout_text, str) and layout_text.strip():
        original.extend(_parse_sfdisk_lines(layout_text))

    entries = manifest.get("entries")
    if isinstance(entries, list):
        for e in entries:
            if isinstance(e, dict) and e.get("type") == "partition":
                original.append(_entry_from_manifest_row(e))

    if not original:
        return {
            **base,
            "status": "review_required",
            "original_layout": [],
            "suggested_layout": [],
            "warnings": [
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

    return {
        **base,
        "status": "ok",
        "original_layout": original,
        "suggested_layout": suggested,
        "warnings": warnings,
    }
