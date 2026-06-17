"""
Rescue backup verify contract — read-only checks, no restore (RS-P1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

CONTRACT_VERSION = 1

DEFAULT_VERIFY_STEPS = (
    "sha256_file",
    "manifest_integrity",
    "image_size_check",
    "image_read_sample",
)


def build_backup_verify_plan(
    *,
    image_path: str = "",
    manifest_path: str = "",
    sha256_path: str = "",
    encrypted: bool = False,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    steps = list(DEFAULT_VERIFY_STEPS)
    if encrypted:
        steps.append("encrypted_container_check")
    if not image_path:
        errors.append({"code": "image_path_missing", "message": "Kein Image-Pfad für Verify."})
    if not manifest_path:
        warnings.append({"code": "manifest_missing", "message": "Manifest fehlt — Verify eingeschränkt."})
    if not sha256_path:
        warnings.append({"code": "sha256_missing", "message": "SHA256-Datei fehlt."})
    status = "blocked" if errors else ("ready" if not warnings else "ready")
    return {
        "contract_version": CONTRACT_VERSION,
        "verify_status": status,
        "verify_required": True,
        "verify_steps": steps,
        "write_operations_required": False,
        "restore_required": False,
        "paths": {
            "image": image_path or None,
            "manifest": manifest_path or None,
            "sha256": sha256_path or None,
        },
        "errors": errors,
        "warnings": warnings,
    }


def validate_verify_preflight(plan: dict[str, Any] | None) -> dict[str, Any]:
    body = plan if isinstance(plan, dict) else {}
    if body.get("verify_status") not in ("ready", "ok"):
        return {
            "ok": False,
            "code": "verify_not_ready",
            "message": "Verify muss vor Execute erfolgreich sein.",
        }
    return {"ok": True, "code": "verify_ready"}
