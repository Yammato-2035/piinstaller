"""
Partitionshelfer API – Festplatten-Scan, Sicherheitsprüfungen, Aktions-Queue (Phase 2).

Nutzt die Logik unter apps/partitionshelfer/core/ (lesend; Schreiben nur nach Freigabe).
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

_PARTITIONS_APP = Path(__file__).resolve().parents[3] / "apps" / "partitionshelfer"


_PKG = "setuphelfer_partitions_core"


def _load_partitions_core() -> tuple[ModuleType, ModuleType]:
    """Lädt apps/partitionshelfer/core ohne Kollision mit backend/core."""
    core_dir = _PARTITIONS_APP / "core"
    if not core_dir.is_dir():
        raise ImportError(f"Partitionshelfer core fehlt: {core_dir}")

    pkg = ModuleType(_PKG)
    pkg.__path__ = [str(core_dir)]
    sys.modules[_PKG] = pkg

    def _load_sub(name: str, filename: str) -> ModuleType:
        path = core_dir / filename
        full_name = f"{_PKG}.{name}"
        spec = importlib.util.spec_from_file_location(full_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Partitionshelfer-Modul nicht ladbar: {path}")
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = _PKG
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)
        setattr(pkg, name, mod)
        return mod

    disk_scanner = _load_sub("disk_scanner", "disk_scanner.py")
    safety_checks = _load_sub("safety_checks", "safety_checks.py")
    return disk_scanner, safety_checks


_disk_scanner, _safety_checks = _load_partitions_core()

Disk = _disk_scanner.Disk
Partition = _disk_scanner.Partition
scan_all_disks = _disk_scanner.scan_all_disks
hat_blockierende_warnung = _safety_checks.hat_blockierende_warnung
pruefe_loeschen = _safety_checks.pruefe_loeschen
pruefe_verkleinern = _safety_checks.pruefe_verkleinern

partition_router = APIRouter(tags=["partitions"])

_queue: list[dict[str, Any]] = []


def _partition_to_dict(part: Partition) -> dict[str, Any]:
    fs = part.fs_info
    children = [_partition_to_dict(c) for c in part.children or []]
    return {
        "name": part.name,
        "size_bytes": part.size_bytes,
        "size_human": part.size_human,
        "fstype": part.fstype,
        "mountpoint": part.mountpoint,
        "label": part.label,
        "uuid": part.uuid,
        "parttypename": part.parttypename,
        "used_bytes": part.used_bytes,
        "free_bytes": part.free_bytes,
        "used_human": part.used_human,
        "free_human": part.free_human,
        "used_percent": part.used_percent,
        "is_mounted": part.is_mounted,
        "is_system_critical": part.is_system_critical,
        "display_name": part.display_name,
        "fs_info": {
            "name": fs["name"],
            "beschreibung": fs["beschreibung"],
            "empfehlung": fs["empfehlung"],
            "farbe": fs["farbe"],
        },
        "children": children,
    }


def _disk_to_dict(disk: Disk) -> dict[str, Any]:
    return {
        "name": disk.name,
        "size_bytes": disk.size_bytes,
        "size_human": disk.size_human,
        "vendor": disk.vendor,
        "model": disk.model,
        "display_name": disk.display_name,
        "partitions": [_partition_to_dict(p) for p in disk.partitions],
    }


def _warnung_to_dict(w) -> dict[str, Any]:
    return {
        "stufe": w.stufe.value,
        "titel": w.titel,
        "erklaerung": w.erklaerung,
        "empfehlung": w.empfehlung,
        "blockiert": w.blockiert,
        "farbe": w.farbe,
        "icon": w.icon,
    }


def _find_partition(name: str) -> Optional[Partition]:
    for disk in scan_all_disks():
        for part in disk.partitions:
            if part.name == name:
                return part
            for child in part.children or []:
                if child.name == name:
                    return child
    return None


@partition_router.get("/scan")
async def get_partition_scan() -> dict[str, Any]:
    try:
        disks = scan_all_disks()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan fehlgeschlagen: {exc}") from exc
    return {
        "disks": [_disk_to_dict(d) for d in disks],
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }


@partition_router.get("/safety-check")
async def get_safety_check(
    partition: str = Query(..., description="Partitionsname z. B. sda1"),
    action: Literal["delete", "format", "resize"] = Query("delete"),
    neue_groesse_bytes: Optional[int] = Query(None, alias="neue_groesse_bytes"),
) -> dict[str, Any]:
    part = _find_partition(partition)
    if part is None:
        raise HTTPException(status_code=404, detail=f"Partition '{partition}' nicht gefunden")

    if action in ("delete", "format"):
        warnungen = pruefe_loeschen(part)
    elif action == "resize":
        if neue_groesse_bytes is None:
            raise HTTPException(
                status_code=400,
                detail="Parameter neue_groesse_bytes erforderlich für resize",
            )
        warnungen = pruefe_verkleinern(part, neue_groesse_bytes)
    else:
        warnungen = pruefe_loeschen(part)

    return {
        "partition_name": partition,
        "warnungen": [_warnung_to_dict(w) for w in warnungen],
        "hat_blockierende": hat_blockierende_warnung(warnungen),
    }


@partition_router.get("/queue")
async def get_queue() -> dict[str, Any]:
    return {"actions": list(_queue)}


@partition_router.delete("/queue")
async def clear_queue() -> dict[str, str]:
    _queue.clear()
    return {"status": "ok"}


@partition_router.delete("/queue/{action_id}")
async def remove_queue_item(action_id: str) -> dict[str, str]:
    global _queue
    before = len(_queue)
    _queue = [a for a in _queue if a.get("id") != action_id]
    if len(_queue) == before:
        raise HTTPException(status_code=404, detail="Aktion nicht gefunden")
    return {"status": "ok"}


class ApplyQueueBody(BaseModel):
    confirmed: bool = False


@partition_router.post("/queue/apply")
async def apply_queue(body: ApplyQueueBody) -> dict[str, Any]:
    if not body.confirmed:
        return {
            "erfolg": 0,
            "fehler": 0,
            "blockiert": len(_queue),
            "message": "Bestätigung erforderlich (confirmed=true).",
        }
    blocked = sum(1 for a in _queue if not a.get("execution_allowed", True))
    if blocked:
        return {
            "erfolg": 0,
            "fehler": 0,
            "blockiert": blocked,
            "message": "Schreiboperationen sind in Phase 2 noch nicht aktiv – Queue unverändert.",
        }
    return {
        "erfolg": 0,
        "fehler": 0,
        "blockiert": 0,
        "message": "Keine ausführbaren Aktionen in der Queue (Phase 2).",
    }
