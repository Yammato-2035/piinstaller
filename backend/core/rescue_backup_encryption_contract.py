"""
Rescue backup encryption contract — no secrets in logs/evidence (RS-P1).
"""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = 1

SUPPORTED_MODES = frozenset({"age", "gpg", "passphrase_later", "no_encryption_for_lab_only", "not_configured"})


def build_encryption_preflight(
    *,
    encryption_requested: bool = True,
    mode: str = "not_configured",
    key_configured: bool = False,
    lab_unencrypted_confirmed: bool = False,
) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    mode_norm = mode if mode in SUPPORTED_MODES else "not_configured"

    if encryption_requested and not key_configured and mode_norm in ("not_configured", "passphrase_later"):
        warnings.append(
            {
                "code": "encryption_key_missing",
                "message": "Verschlüsselung angefordert, Schlüssel/Passphrase noch nicht konfiguriert.",
            }
        )
    if mode_norm == "no_encryption_for_lab_only" and not lab_unencrypted_confirmed:
        errors.append(
            {"code": "lab_unencrypted_not_confirmed", "message": "Lab-Backup ohne Verschlüsselung nicht bestätigt."}
        )

    if encryption_requested and mode_norm == "not_configured":
        status = "missing"
    elif key_configured:
        status = "configured"
    elif mode_norm == "passphrase_later":
        status = "deferred"
    elif mode_norm == "no_encryption_for_lab_only" and lab_unencrypted_confirmed:
        status = "lab_unencrypted_allowed"
    else:
        status = "blocked"

    execute_allowed = status == "configured" or (
        status == "lab_unencrypted_allowed" and lab_unencrypted_confirmed
    )

    return {
        "contract_version": CONTRACT_VERSION,
        "encryption_status": status,
        "encryption_required": encryption_requested,
        "mode": mode_norm,
        "key_material_logged": False,
        "evidence_contains_secret": False,
        "execute_allowed": False if encryption_requested else execute_allowed,
        "blocks_execute": encryption_requested and status in ("missing", "deferred", "blocked"),
        "warnings": warnings,
        "errors": errors,
    }
