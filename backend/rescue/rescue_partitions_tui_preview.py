"""
Read-only partitions preview for rescue TUI / autocapture.

PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006 — Partitionshelfer on stick without writes.

Never calls parted/sfdisk/mkfs/wipefs/dd. ``write_allowed`` is always False.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RESCUE_PARTITIONS_TUI_PREVIEW_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lsblk_json() -> dict[str, Any]:
    try:
        out = subprocess.check_output(
            [
                "lsblk",
                "--json",
                "--bytes",
                "-o",
                "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINT,MODEL,SERIAL,TRAN,RM,PARTTYPE",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        data = json.loads(out or "{}")
        return data if isinstance(data, dict) else {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError):
        return {}


def _flatten(nodes: list[dict[str, Any]], parent: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for n in nodes:
        path = n.get("path") or (f"/dev/{n['name']}" if n.get("name") else None)
        row = {
            "name": n.get("name"),
            "path": path,
            "type": n.get("type"),
            "size_bytes": n.get("size"),
            "fstype": n.get("fstype"),
            "label": n.get("label"),
            "uuid": n.get("uuid"),
            "mountpoint": n.get("mountpoint"),
            "model": n.get("model"),
            "serial": n.get("serial"),
            "tran": n.get("tran"),
            "rm": n.get("rm"),
            "parttype": n.get("parttype"),
            "parent": parent,
        }
        rows.append(row)
        children = n.get("children") or []
        if children and path:
            rows.extend(_flatten(children, parent=path))
        elif children and n.get("name"):
            rows.extend(_flatten(children, parent=f"/dev/{n['name']}"))
    return rows


def build_partitions_tui_preview(
    *,
    disk_discovery: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact, redaction-safe partition inventory for TUI/evidence."""
    tree = _lsblk_json()
    devices = _flatten(list(tree.get("blockdevices") or []))
    disks = [d for d in devices if d.get("type") == "disk"]
    parts = [d for d in devices if d.get("type") == "part"]

    # Prefer existing disk-discovery classification when provided.
    classified: list[dict[str, Any]] = []
    if isinstance(disk_discovery, dict):
        for item in disk_discovery.get("devices") or []:
            if isinstance(item, dict):
                classified.append(
                    {
                        "path": item.get("path") or item.get("name"),
                        "role": item.get("role") or item.get("classification"),
                        "label": item.get("label"),
                        "fstype": item.get("fstype"),
                        "size": item.get("size"),
                    }
                )

    # Safety facade snapshot (always write-blocked).
    safety: dict[str, Any] = {
        "write_allowed": False,
        "phase": "preview_only",
        "forbidden_ops": ["parted", "sfdisk", "mkfs", "wipefs", "dd", "sgdisk"],
    }
    probe_target = next((d.get("path") for d in disks if d.get("path")), None)
    if probe_target:
        try:
            from core.partition_storage_facade import build_partition_target_safety_context

            ctx = build_partition_target_safety_context(target_device=str(probe_target))
            if isinstance(ctx, dict):
                safety["facade_status"] = ctx.get("status")
                safety["probe_target"] = probe_target
                # Hard rule for this module: never advertise writes.
                safety["write_allowed"] = False
                safety["facade_write_allowed_raw"] = bool(ctx.get("write_allowed", False))
        except Exception as exc:  # noqa: BLE001 — preview must not crash TUI
            safety["facade_error"] = f"{type(exc).__name__}: {exc}"
            safety["write_allowed"] = False

    return {
        "schema_version": RESCUE_PARTITIONS_TUI_PREVIEW_VERSION,
        "module": "rescue_partitions_tui_preview",
        "collected_at": _utc_now(),
        "write_allowed": False,
        "partition_rewritten": False,
        "filesystem_reformatted": False,
        "disk_count": len(disks),
        "partition_count": len(parts),
        "disks": disks,
        "partitions": parts,
        "classified_from_disk_discovery": classified,
        "safety": safety,
        "operator_note_de": (
            "Nur Anzeige/Inventur. Partitionieren, Formatieren und Wipe sind auf dem "
            "Rettungsstick in dieser Phase blockiert (write_allowed=false)."
        ),
        "secrets_exposed": False,
    }


def write_partitions_preview_json(path: Path, preview: dict[str, Any] | None = None) -> Path:
    payload = preview if preview is not None else build_partitions_tui_preview()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def format_partitions_tui_message(preview: dict[str, Any]) -> str:
    lines = [
        "Partitionshelfer (nur Lesen)",
        f"Datenträger: {preview.get('disk_count')}  Partitionen: {preview.get('partition_count')}",
        f"Schreiben erlaubt: {preview.get('write_allowed')}",
        "",
    ]
    for d in (preview.get("disks") or [])[:8]:
        size = d.get("size_bytes")
        size_h = f"{int(size) / (1024**3):.1f}G" if isinstance(size, int) else "?"
        lines.append(
            f"- {d.get('path') or d.get('name')}  {size_h}  "
            f"{(d.get('model') or '').strip() or 'disk'}  "
            f"tran={d.get('tran') or '—'}"
        )
        for p in (preview.get("partitions") or []):
            if p.get("parent") != (d.get("path") or f"/dev/{d.get('name')}"):
                continue
            psz = p.get("size_bytes")
            psz_h = f"{int(psz) / (1024**3):.1f}G" if isinstance(psz, int) else "?"
            lines.append(
                f"    {p.get('path') or p.get('name')}  {psz_h}  "
                f"{p.get('fstype') or '—'}  {p.get('label') or ''}"
            )
    lines.append("")
    lines.append(str(preview.get("operator_note_de") or ""))
    return "\n".join(lines)
