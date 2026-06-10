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

from core.partition_storage_facade import (
    build_partition_target_safety_context,
    read_backup_manifest_readonly,
)
from core.storage_role_classification import (
    classify_scan_disks,
    find_classification_for_target,
)

_PARTITIONS_APP = Path(__file__).resolve().parents[3] / "apps" / "partitionshelfer"


_PKG = "setuphelfer_partitions_core"


def _load_partitions_core() -> dict[str, ModuleType]:
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

    return {
        "disk_scanner": _load_sub("disk_scanner", "disk_scanner.py"),
        "safety_checks": _load_sub("safety_checks", "safety_checks.py"),
        "partition_hardstop": _load_sub("partition_hardstop", "partition_hardstop.py"),
        "manifest_layout_preview": _load_sub(
            "manifest_layout_preview", "manifest_layout_preview.py"
        ),
        "restore_handoff_contract": _load_sub(
            "restore_handoff_contract", "restore_handoff_contract.py"
        ),
    }


_core = _load_partitions_core()
_disk_scanner = _core["disk_scanner"]
_safety_checks = _core["safety_checks"]
_partition_hardstop = _core["partition_hardstop"]
_manifest_layout_preview = _core["manifest_layout_preview"]
_restore_handoff_contract = _core["restore_handoff_contract"]

build_partition_hardstop_context = _partition_hardstop.build_partition_hardstop_context
evaluate_partition_hardstops = _partition_hardstop.evaluate_partition_hardstops
build_manifest_layout_preview = _manifest_layout_preview.build_manifest_layout_preview
build_partition_restore_handoff = _restore_handoff_contract.build_partition_restore_handoff

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


def _disk_to_dict(disk: Disk, *, storage_role: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "name": disk.name,
        "size_bytes": disk.size_bytes,
        "size_human": disk.size_human,
        "vendor": disk.vendor,
        "model": disk.model,
        "display_name": disk.display_name,
        "tran": getattr(disk, "tran", None),
        "removable": bool(getattr(disk, "removable", False)),
        "partitions": [_partition_to_dict(p) for p in disk.partitions],
    }
    if storage_role:
        base["storage_role"] = storage_role
    return base


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
    disk_dicts = [_disk_to_dict(d) for d in disks]
    roles = classify_scan_disks(disk_dicts)
    merged = [
        _disk_to_dict(d, storage_role=role)
        for d, role in zip(disks, roles, strict=True)
    ]
    return {
        "disks": merged,
        "storage_roles": roles,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }


@partition_router.get("/storage-roles")
async def get_storage_roles() -> dict[str, Any]:
    try:
        disks = scan_all_disks()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan fehlgeschlagen: {exc}") from exc
    disk_dicts = [_disk_to_dict(d) for d in disks]
    roles = classify_scan_disks(disk_dicts)
    return {
        "devices": roles,
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


class ManifestLayoutPreviewBody(BaseModel):
    manifest: dict[str, Any] | None = None
    target_device: str | None = None
    manifest_path: str | None = None


class RestoreHandoffPreviewBody(BaseModel):
    target_device: str
    partition_plan_preview: dict[str, Any] | None = None
    hardstop_result: dict[str, Any] | None = None
    manifest_layout_preview: dict[str, Any] | None = None
    backup_manifest_ref: str | None = None
    verify_evidence: dict[str, Any] | None = None
    operator_override: bool = False


@partition_router.get("/hardstop-preview")
async def get_hardstop_preview(
    target_device: str = Query(..., description="Ziel z. B. /dev/sda oder sda1"),
    backup_source_device: str | None = Query(None),
    backup_archive_path: str | None = Query(None),
    manifest_path: str | None = Query(None),
    planned_action: str | None = Query(None),
    target_classification: str | None = Query(None),
    system_disk: bool = Query(False),
    identity_unknown: bool = Query(False),
    smart_state: str | None = Query(None, description="OK|WARNING|FAILED|UNKNOWN"),
    use_inspect: bool = Query(False, description="Inspect-Ergebnis für write_guard einbeziehen"),
    operator_override: bool = Query(False, description="Nie Freigabe – nur dokumentierter Hinweis"),
) -> dict[str, Any]:
    smart_summary: dict[str, Any] | None = None
    if smart_state:
        smart_summary = {"state": smart_state.upper()}
    storage_classification: dict[str, Any] = {}
    if target_classification:
        storage_classification["target_classification"] = target_classification
    if system_disk:
        storage_classification["system_disk"] = True
    if identity_unknown:
        storage_classification["identity_unknown"] = True

    safety_ctx = build_partition_target_safety_context(
        target_device,
        backup_source_device=backup_source_device,
        backup_archive_path=backup_archive_path,
        manifest_path=manifest_path,
        use_inspect=use_inspect,
        operator_override=operator_override,
        system_disk_hint=system_disk,
        identity_unknown_hint=identity_unknown,
        target_classification_hint=target_classification,
    )
    facade_class = safety_ctx.get("storage_classification") or {}
    storage_classification = {**facade_class, **storage_classification}

    try:
        scanned = [_disk_to_dict(d) for d in scan_all_disks()]
        auto_role = find_classification_for_target(
            scanned,
            target_device,
            backup_source_device=backup_source_device,
        )
        if auto_role:
            storage_classification = {**auto_role, **storage_classification}
    except Exception:
        pass

    ctx = build_partition_hardstop_context(
        target_device=target_device,
        backup_source_device=backup_source_device,
        backup_archive_path=backup_archive_path,
        manifest_path=manifest_path,
        storage_classification=storage_classification or None,
        smart_summary=smart_summary,
        planned_action=planned_action,
    )
    ctx["storage_safety_context"] = safety_ctx
    result = evaluate_partition_hardstops(ctx)
    return {
        "context": ctx,
        "evaluation": result,
        "storage_safety": safety_ctx,
        "write_allowed": False,
    }


@partition_router.post("/manifest-layout-preview")
async def post_manifest_layout_preview(body: ManifestLayoutPreviewBody) -> dict[str, Any]:
    preview = build_manifest_layout_preview(
        body.manifest,
        body.target_device,
        manifest_path=body.manifest_path,
        manifest_reader=read_backup_manifest_readonly,
    )
    return {**preview, "write_allowed": False}


@partition_router.post("/restore-handoff-preview")
async def post_restore_handoff_preview(body: RestoreHandoffPreviewBody) -> dict[str, Any]:
    safety_ctx: dict[str, Any] | None = None
    if body.hardstop_result is None:
        safety_ctx = build_partition_target_safety_context(
            body.target_device,
            operator_override=body.operator_override,
        )
    handoff = build_partition_restore_handoff(
        partition_plan_preview=body.partition_plan_preview,
        hardstop_result=body.hardstop_result,
        manifest_layout_preview=body.manifest_layout_preview,
        target_device=body.target_device,
        backup_manifest_ref=body.backup_manifest_ref,
        verify_evidence=body.verify_evidence,
        storage_safety_context=safety_ctx,
        operator_override=body.operator_override,
    )
    return {**handoff, "write_allowed": False}


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
