"""
Partition-Hardstop-Layer (Phase 2) – reine Prüf-/Entscheidungslogik, keine Schreibzugriffe.

SMART: nur über übergebenes ``smart_summary`` (Adapter zu backend/modules/inspect_storage.smart_classify_disk).
Storage-Klassifikation: optional vom Aufrufer (storage_facade / write_guard), keine eigenen lsblk-Duplikate hier.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

_WRITE_ACTIONS = frozenset(
    {
        "delete",
        "format",
        "resize",
        "partition",
        "mkfs",
        "write",
        "apply",
        "wipe",
        "create",
    }
)

RiskLevel = Literal["green", "yellow", "red"]
HardstopStatus = Literal["ok", "review_required", "blocked"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_dev(device: str | None) -> str:
    if not device:
        return ""
    d = str(device).strip()
    if not d:
        return ""
    if not d.startswith("/dev/"):
        d = f"/dev/{d.lstrip('/')}"
    return d


def _disk_of_dev(device: str) -> str:
    """Grober Parent-Disk-Pfad für Partitionen (z. B. /dev/sda1 → /dev/sda)."""
    dev = _norm_dev(device)
    if not dev:
        return ""
    if dev.startswith("/dev/nvme") and "p" in dev.split("/")[-1]:
        base = dev.rsplit("p", 1)[0]
        return base if base.startswith("/dev/") else dev
    name = dev.removeprefix("/dev/")
    if name and name[-1].isdigit() is False:
        return dev
    disk = name.rstrip("0123456789")
    return f"/dev/{disk}" if disk else dev


def _devices_same_disk(a: str, b: str) -> bool:
    na, nb = _norm_dev(a), _norm_dev(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    return _disk_of_dev(na) == _disk_of_dev(nb) or na == _disk_of_dev(nb) or nb == _disk_of_dev(na)


def normalize_smart_status(smart_summary: dict[str, Any] | None) -> str:
    """
    Normalisiert SMART auf: missing | unknown | ok | warning | failing.

    Erwartet optional Felder aus inspect_storage.smart_classify_disk:
    state (OK/FAILED/WARNING/UNKNOWN), risk_code, smart_status.
    """
    if not smart_summary:
        return "missing"
    if isinstance(smart_summary.get("smart_status"), str):
        raw = smart_summary["smart_status"].strip().lower()
        if raw in ("ok", "passed", "healthy"):
            return "ok"
        if raw in ("warning", "yellow", "degraded"):
            return "warning"
        if raw in ("failing", "critical", "failed"):
            return "failing"
        if raw in ("missing", "unknown", "not_available", "unavailable"):
            return "missing" if raw == "missing" else "unknown"

    state = str(smart_summary.get("state") or "").upper()
    risk = str(smart_summary.get("risk_code") or "").lower()
    if state == "OK" or "smart.ok" in risk:
        return "ok"
    if state == "FAILED" or "critical" in risk or "failing" in risk:
        return "failing"
    if state == "WARNING" or "warning" in risk:
        return "warning"
    if state == "UNKNOWN" or "not_available" in risk:
        return "unknown"
    return "unknown"


def build_partition_hardstop_context(
    *,
    target_device: str | None = None,
    backup_source_device: str | None = None,
    backup_archive_path: str | None = None,
    manifest_path: str | None = None,
    storage_classification: dict[str, Any] | None = None,
    smart_summary: dict[str, Any] | None = None,
    planned_action: str | None = None,
) -> dict[str, Any]:
    smart_status = normalize_smart_status(smart_summary)
    classification = storage_classification if isinstance(storage_classification, dict) else {}
    target_class = str(
        classification.get("target_classification")
        or classification.get("classification")
        or classification.get("role")
        or ""
    ).strip()

    return {
        "target_device": _norm_dev(target_device) or (target_device or "").strip(),
        "backup_source_device": _norm_dev(backup_source_device) or (backup_source_device or "").strip(),
        "backup_archive_path": (backup_archive_path or "").strip() or None,
        "manifest_path": (manifest_path or "").strip() or None,
        "same_as_backup_source": _devices_same_disk(
            target_device or "", backup_source_device or ""
        ),
        "smart_status": smart_status,
        "smart_summary": smart_summary,
        "target_classification": target_class,
        "storage_classification": classification,
        "planned_action": (planned_action or "").strip().lower() or None,
        "generated_at": _utc_now(),
        "write_allowed": False,
    }


def evaluate_partition_hardstops(context: dict[str, Any]) -> dict[str, Any]:
    hardstops: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    codes: list[str] = []

    target = _norm_dev(context.get("target_device"))
    backup_src = _norm_dev(context.get("backup_source_device"))
    smart_status = str(context.get("smart_status") or "missing")
    classification = context.get("storage_classification") or {}
    planned = (context.get("planned_action") or "").strip().lower()
    explicit_write_release = bool(context.get("explicit_write_release"))

    def _stop(code: str, message: str) -> None:
        codes.append(code)
        hardstops.append({"code": code, "message": message})

    def _warn(code: str, message: str) -> None:
        codes.append(code)
        warnings.append({"code": code, "message": message})

    _warn(
        "partition.info.readonly_phase2",
        "Phase 2: nur Plan/Preview/Validation – keine Partitionierungs-Schreiboperationen.",
    )

    if not target:
        _stop("partition.hardstop.target_missing", "Zielgerät fehlt.")

    if backup_src and target and (target == backup_src or _devices_same_disk(target, backup_src)):
        _stop(
            "partition.hardstop.partition_target_is_backup_source",
            "Partitionierungsziel darf nicht die Backup-Quelle sein.",
        )

    archive = (context.get("backup_archive_path") or "").strip()
    if archive and target:
        # Archivpfad allein blockiert nicht; Kombination mit gleicher Quelle oben abgedeckt.
        pass

    target_identity = str(classification.get("target_identity") or "").strip().lower()
    identity_unknown = bool(classification.get("identity_unknown")) or target_identity in (
        "unknown",
        "unresolved",
    )
    if target and identity_unknown:
        _stop(
            "partition.hardstop.target_identity_unknown",
            "Zielidentität unbekannt – kein Write-Kontext.",
        )

    is_system = bool(
        classification.get("system_disk")
        or classification.get("system_disk_candidate")
        or classification.get("is_system_disk")
        or str(classification.get("target_classification") or "").lower()
        in ("system", "system_disk", "boot_disk")
    )
    if target and is_system:
        _stop(
            "partition.hardstop.target_is_system_disk",
            "Ziel ist als Systemdisk klassifiziert.",
        )

    if smart_status in ("failing", "critical"):
        _stop("partition.hardstop.smart_failing", "SMART meldet kritischen Zustand.")
    elif smart_status == "warning":
        _warn("partition.warning.smart_yellow", "SMART meldet Warnung – manuelle Prüfung.")
    elif smart_status in ("missing", "unknown"):
        _warn(
            "partition.warning.manual_review_required",
            "SMART-Status unbekannt – manuelle Prüfung vor späteren Writes.",
        )

    if planned in _WRITE_ACTIONS and not explicit_write_release:
        _stop(
            "partition.hardstop.write_action_not_released",
            f"Geplante Aktion '{planned}' ohne explizite Freigabe blockiert.",
        )

    if hardstops:
        status: HardstopStatus = "blocked"
        risk: RiskLevel = "red"
    elif warnings:
        status = "review_required"
        risk = "yellow"
    else:
        status = "ok"
        risk = "green"

    return {
        "status": status,
        "hardstops": hardstops,
        "warnings": warnings,
        "risk_level": risk,
        "write_allowed": False,
        "codes": codes,
        "target_device": target or context.get("target_device"),
        "generated_at": _utc_now(),
    }
