"""
Read-only Storage-Facade für den Partitionshelfer.

Bündelt write_guard, backup_before_write und Pfad-/Klassifikations-Hinweise
ohne Mount, parted, mkfs oder andere Schreib-/Low-Level-Aktionen.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from core.backup_before_write_gate import evaluate_backup_before_write_requirement
from core.safe_device import write_safe_prefixes_resolved
from safety.write_guard import evaluate_write_target

FacadeStatus = Literal["ok", "review_required", "blocked"]

_FORBIDDEN_PATH_PREFIXES = (
    "/",
    "/boot",
    "/tmp",
    "/var",
    "/usr",
    "/etc",
    "/home",
    "/opt",
    "/run",
    "/sys",
    "/proc",
    "/dev",
)
_MEDIA_PREFIX = "/media/"


def _norm_dev(device: str | None) -> str:
    if not device:
        return ""
    d = str(device).strip()
    if not d:
        return ""
    if d.startswith("/") and not d.startswith("/dev/"):
        return d
    if not d.startswith("/dev/"):
        d = f"/dev/{d.lstrip('/')}"
    return d


def _is_path_target(target: str) -> bool:
    return bool(target) and target.startswith("/") and not target.startswith("/dev/")


def _path_under_any_prefix(p: Path, prefixes: tuple[Path, ...]) -> bool:
    rp = p.resolve()
    for root in prefixes:
        br = root.resolve()
        try:
            rp.relative_to(br)
            return True
        except ValueError:
            if rp == br:
                return True
    return False


def read_backup_manifest_readonly(manifest_path: str | None) -> tuple[dict[str, Any] | None, str | None]:
    """
    Liest MANIFEST.json nur von explizitem, allowlist-konformem Pfad (kein Archiv-Extract).
    """
    if not manifest_path or not str(manifest_path).strip():
        return None, "path_missing"
    raw = Path(str(manifest_path).strip())
    if ".." in raw.parts:
        return None, "path_traversal"
    try:
        resolved = raw.resolve(strict=False)
    except OSError:
        return None, "path_resolve_failed"
    if resolved.name != "MANIFEST.json":
        return None, "not_manifest_filename"
    prefixes = write_safe_prefixes_resolved()
    if not _path_under_any_prefix(resolved, prefixes):
        return None, "path_not_allowlisted"
    if not resolved.is_file():
        return None, "not_found"
    try:
        text = resolved.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, "invalid_json"
    except OSError:
        return None, "read_failed"
    if not isinstance(data, dict):
        return None, "invalid_manifest_shape"
    return data, None


def _inspect_to_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    return dict(result)


def _collect_inspect_result() -> dict[str, Any] | None:
    try:
        import importlib.util
        import sys

        collector_path = Path(__file__).resolve().parent.parent / "inspect" / "collector.py"
        spec = importlib.util.spec_from_file_location(
            "setuphelfer_partition_inspect_collector", collector_path
        )
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules["setuphelfer_partition_inspect_collector"] = mod
        spec.loader.exec_module(mod)
        return _inspect_to_dict(mod.collect_inspect_result())
    except Exception:
        return None


def _path_hardstops(target: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    hardstops: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if target == "/":
        hardstops.append(
            {
                "code": "partition.facade.live_root_blocked",
                "message": "Live-Root (/) ist kein Partitionierungsziel.",
            }
        )
        return hardstops, warnings
    if target.startswith(_MEDIA_PREFIX):
        warnings.append(
            {
                "code": "partition.facade.media_mount_not_auto_allowed",
                "message": "Pfade unter /media/ werden nicht pauschal freigegeben.",
            }
        )
        return hardstops, warnings
    for prefix in _FORBIDDEN_PATH_PREFIXES:
        if prefix == "/":
            continue
        if target == prefix or target.startswith(prefix + "/"):
            hardstops.append(
                {
                    "code": "partition.facade.system_path_blocked",
                    "message": f"Systempfad {target} ist als Ziel blockiert.",
                }
            )
            break
    return hardstops, warnings


def _write_guard_to_classification(
    target: str, wg: dict[str, Any], *, operator_override: bool
) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    """Mappt write_guard auf storage_classification + Hardstops (nie allowed für Partition-Writes)."""
    hardstops: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    rc = str(wg.get("reason_code") or "")
    allowed = wg.get("allowed") is True

    classification: dict[str, Any] = {
        "write_guard_reason": rc,
        "write_guard_allowed": allowed,
        "target_identity": "unknown",
    }

    if operator_override:
        warnings.append(
            {
                "code": "partition.facade.operator_override_never_allowed",
                "message": "Operator-Hinweis erzeugt keine automatische Freigabe.",
            }
        )

    if rc == "SAFETY_SYSTEM_DISK":
        classification.update(
            system_disk=True,
            target_classification="system_disk",
            target_identity="system_disk",
        )
        hardstops.append(
            {
                "code": "partition.hardstop.target_is_system_disk",
                "message": "Ziel ist Systemdisk (write_guard).",
            }
        )
    elif rc == "SAFETY_LIVE_SYSTEM":
        classification.update(system_disk=True, target_classification="live_system")
        hardstops.append(
            {
                "code": "partition.facade.live_root_blocked",
                "message": "Live-System-Mount erkannt – Ziel blockiert.",
            }
        )
    elif rc == "SAFETY_BACKUP_TARGET_OK":
        classification.update(
            target_classification="backup_medium",
            target_identity="backup_medium",
        )
        warnings.append(
            {
                "code": "partition.hardstop.backup_medium_as_target",
                "message": "Backup-Medium als Partitionierungsziel – manuelle Prüfung.",
            }
        )
    elif rc == "SAFETY_UNKNOWN_DEVICE":
        classification.update(identity_unknown=True, target_identity="unknown")
        hardstops.append(
            {
                "code": "partition.hardstop.target_identity_unknown",
                "message": "Gerät unbekannt oder nicht klassifizierbar.",
            }
        )
    elif rc == "SAFETY_WINDOWS_DETECTED":
        classification.update(target_classification="windows_data")
        warnings.append(
            {
                "code": "partition.facade.windows_detected",
                "message": "Windows-Datenträger erkannt – keine automatische Freigabe.",
            }
        )
    elif allowed and rc in ("SAFETY_EMPTY_DISK",):
        classification.update(target_classification="empty_disk", target_identity="empty")
        warnings.append(
            {
                "code": "partition.facade.empty_disk_review",
                "message": "Leere Platte – nur Preview, kein automatischer Write.",
            }
        )
    elif allowed:
        warnings.append(
            {
                "code": "partition.facade.write_guard_never_partition_allowed",
                "message": "write_guard-Freigabe gilt nicht für Partitions-Schreiben.",
            }
        )
    else:
        classification.update(identity_unknown=True)
        hardstops.append(
            {
                "code": "partition.hardstop.target_identity_unknown",
                "message": f"Write-Guard blockiert ({rc or 'unknown'}).",
            }
        )

    return classification, hardstops, warnings


def build_partition_target_safety_context(
    target_device: str,
    *,
    backup_source_device: str | None = None,
    backup_archive_path: str | None = None,
    manifest_path: str | None = None,
    inspect_result: dict[str, Any] | None = None,
    use_inspect: bool = False,
    backup_evidence: dict[str, Any] | None = None,
    operator_override: bool = False,
    system_disk_hint: bool = False,
    identity_unknown_hint: bool = False,
    target_classification_hint: str | None = None,
    existing_filesystems: bool | None = None,
    existing_os_indicators: bool | None = None,
    user_data_indicators: bool | None = None,
) -> dict[str, Any]:
    """
    Einheitlicher read-only Safety-Kontext für Hardstop/Manifest/Handoff.
    """
    errors: list[str] = []
    hardstops: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    normalized = _norm_dev(target_device) or str(target_device or "").strip()
    is_path = _is_path_target(normalized)

    insp = inspect_result
    if use_inspect and insp is None:
        insp = _collect_inspect_result()

    classification: dict[str, Any] = {}
    if target_classification_hint:
        classification["target_classification"] = target_classification_hint
    if system_disk_hint:
        classification["system_disk"] = True
    if identity_unknown_hint:
        classification["identity_unknown"] = True

    write_guard_result: dict[str, Any] = {}
    if insp and normalized and not is_path:
        write_guard_result = evaluate_write_target(normalized, insp)
        wg_class, wg_hs, wg_warn = _write_guard_to_classification(
            normalized, write_guard_result, operator_override=operator_override
        )
        classification = {**wg_class, **classification}
        hardstops.extend(wg_hs)
        warnings.extend(wg_warn)

    if is_path and normalized:
        phs, pws = _path_hardstops(normalized)
        hardstops.extend(phs)
        warnings.extend(pws)

    backup_before = evaluate_backup_before_write_requirement(
        target_classification=classification.get("target_classification"),
        existing_filesystems=existing_filesystems,
        existing_os_indicators=existing_os_indicators,
        user_data_indicators=user_data_indicators,
        backup_evidence=backup_evidence,
        operator_override=operator_override,
    )
    if backup_before.get("status") == "blocked":
        for err in backup_before.get("errors") or []:
            hardstops.append(
                {
                    "code": "partition.facade.backup_before_write",
                    "message": str(err),
                }
            )
    elif backup_before.get("status") == "review_required":
        for w in backup_before.get("warnings") or []:
            warnings.append(
                {
                    "code": "partition.facade.backup_before_write",
                    "message": str(w),
                }
            )

    if operator_override:
        warnings.append(
            {
                "code": "partition.facade.operator_override_never_allowed",
                "message": "Operator-Override erlaubt keine Partition-Writes.",
            }
        )

    if hardstops:
        status: FacadeStatus = "blocked"
    elif warnings:
        status = "review_required"
    else:
        status = "ok"

    return {
        "status": status,
        "target_device": normalized or target_device,
        "normalized_target": normalized or target_device,
        "write_allowed": False,
        "decision_source": "core_storage_facade",
        "device": {"path": normalized} if normalized else {},
        "mounts": [],
        "filesystem": {},
        "hardstops": hardstops,
        "warnings": warnings,
        "errors": errors,
        "core_results": {
            "safe_device": {"manifest_path": manifest_path, "backup_archive_path": backup_archive_path},
            "write_guard": write_guard_result,
            "allowlist": {"prefixes": [str(p) for p in write_safe_prefixes_resolved()]},
            "backup_before_write": backup_before,
        },
        "storage_classification": classification,
        "backup_source_device": _norm_dev(backup_source_device) or backup_source_device,
    }
