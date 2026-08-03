"""
OS image checksum/signature verification preview — no download, no real hashing
of a downloaded file (there is no downloaded file in this phase).

PI-RS-HW-COMPAT-PROVISION-001 Phase 13 (verifier half).

This module models *how* verification would proceed once a signed image and a
real local file exist — it never fetches anything and never invents a checksum.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

OS_IMAGE_VERIFIER_VERSION = 1


def compute_sha256_of_local_file(path: Path) -> str | None:
    """Real SHA256 of an already-present local file (e.g. an operator-provided,
    already-downloaded image). Never triggers a download."""
    if not path.exists() or not path.is_file():
        return None
    try:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def build_verification_preview(
    *, catalog_entry: dict[str, Any], local_file_sha256: str | None = None
) -> dict[str, Any]:
    """Compare an (optional) locally computed hash against the catalog's expected
    hash. If the catalog has no hash yet (``sha256: null`` placeholder — see
    os_catalog.json note), verification can only report ``status=no_reference_hash``,
    never a false "verified"."""
    expected = catalog_entry.get("sha256")
    signature_required = catalog_entry.get("signature_required", True)

    if not expected:
        status = "no_reference_hash_in_catalog"
    elif local_file_sha256 is None:
        status = "no_local_file_to_verify"
    elif local_file_sha256.lower() == expected.lower():
        status = "hash_match"
    else:
        status = "hash_mismatch"

    return {
        "image_id": catalog_entry.get("image_id"),
        "verification_status": status,
        "signature_required": signature_required,
        "signature_verified": False,  # never true without a real signature check implementation
        "download_performed": False,
    }


def build_os_image_verifier_diagnostics() -> dict[str, Any]:
    return {
        "verifier_version": OS_IMAGE_VERIFIER_VERSION,
        "module": "provisioning.os_image_verifier",
        "download_performed": False,
        "invents_checksums": False,
    }


__all__ = [
    "OS_IMAGE_VERIFIER_VERSION",
    "compute_sha256_of_local_file",
    "build_verification_preview",
    "build_os_image_verifier_diagnostics",
]
