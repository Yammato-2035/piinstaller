"""Distro profile registry + Mint ISO cache contract (PI-RS-INSTALL-ASSISTANT-001).

Download policy: no blind write. Operator must start any fetch. SHA256 is mandatory for valid.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1

# Cache root relative to SETUP_LOGS (or override via env/caller)
DEFAULT_ISO_CACHE_REL = Path("setuphelfer/iso-cache")

DISTRO_PROFILES: dict[str, dict[str, Any]] = {
    "linux_mint": {
        "id": "linux_mint",
        "display_name": "Linux Mint",
        "capability": "preview",
        "support": "supported",
        "p0_executable_prepared": True,
        "arch": "amd64",
        "official_source_hint": "https://linuxmint.com/download.php",
        "requires_sha256": True,
    },
    "ubuntu_server_lts": {
        "id": "ubuntu_server_lts",
        "display_name": "Ubuntu Server LTS",
        "capability": "preview",
        "support": "stub",
        "p0_executable_prepared": False,
        "arch": "amd64",
        "official_source_hint": "https://ubuntu.com/download/server",
        "requires_sha256": True,
    },
    "ubuntu_server": {
        "id": "ubuntu_server",
        "display_name": "Ubuntu Server",
        "capability": "preview",
        "support": "stub",
        "p0_executable_prepared": False,
        "arch": "amd64",
        "official_source_hint": "https://ubuntu.com/download/server",
        "requires_sha256": True,
    },
    "debian": {
        "id": "debian",
        "display_name": "Debian",
        "capability": "preview",
        "support": "stub",
        "p0_executable_prepared": False,
        "arch": "amd64",
        "official_source_hint": "https://www.debian.org/distrib/",
        "requires_sha256": True,
    },
}


def list_distro_profiles() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "profiles": list(DISTRO_PROFILES.values()),
        "p0_distro": "linux_mint",
        "linux_install_capability": "preview",
        "auto_download_allowed": False,
    }


def get_distro_profile(profile_id: str) -> dict[str, Any] | None:
    return DISTRO_PROFILES.get(profile_id)


def iso_cache_path(logs_root: Path | str, profile_id: str) -> Path:
    return Path(logs_root) / DEFAULT_ISO_CACHE_REL / profile_id


def resolve_iso_status(
    *,
    profile_id: str,
    logs_root: Path | str | None = None,
    iso_path: str | None = None,
    sha256_expected: str | None = None,
    sha256_actual: str | None = None,
) -> dict[str, Any]:
    profile = get_distro_profile(profile_id)
    if not profile:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "unknown_profile",
            "profile_id": profile_id,
            "install_allowed": False,
        }
    cache_dir = str(iso_cache_path(logs_root or "/media/SETUP_LOGS", profile_id))
    path = iso_path
    if not path and logs_root:
        cand = iso_cache_path(logs_root, profile_id)
        if cand.is_dir():
            isos = sorted(cand.glob("*.iso"))
            path = str(isos[0]) if isos else None
    if not path:
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "status": "missing",
            "profile_id": profile_id,
            "cache_dir": cache_dir,
            "iso_path": None,
            "sha256_ok": False,
            "capability": profile["capability"],
            "support": profile["support"],
            "install_allowed": False,
            "auto_download_allowed": False,
        }
    sha_ok = bool(
        sha256_expected and sha256_actual and sha256_expected.lower() == sha256_actual.lower()
    )
    if sha256_expected and sha256_actual and not sha_ok:
        status = "corrupt"
    elif sha_ok:
        status = "valid"
    else:
        status = "review_required"
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "profile_id": profile_id,
        "cache_dir": cache_dir,
        "iso_path": path,
        "sha256_ok": sha_ok,
        "sha256_expected": sha256_expected,
        "capability": profile["capability"],
        "support": profile["support"],
        "install_allowed": status == "valid" and profile["p0_executable_prepared"],
        "auto_download_allowed": False,
    }


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def verify_cached_iso(
    *,
    profile_id: str,
    iso_path: str,
    sha256_expected: str,
    compute_actual: bool = False,
    sha256_actual: str | None = None,
) -> dict[str, Any]:
    path = Path(iso_path)
    if not path.is_file():
        return resolve_iso_status(
            profile_id=profile_id,
            iso_path=None,
            sha256_expected=sha256_expected,
        )
    actual = sha256_actual
    if compute_actual:
        actual = sha256_file(path)
    return resolve_iso_status(
        profile_id=profile_id,
        iso_path=str(path),
        sha256_expected=sha256_expected,
        sha256_actual=actual,
    )


def download_policy_gate(*, operator_started: bool, profile_id: str) -> dict[str, Any]:
    profile = get_distro_profile(profile_id)
    if not profile:
        return {"allowed": False, "reason": "unknown_profile"}
    if not operator_started:
        return {
            "allowed": False,
            "reason": "operator_start_required",
            "auto_download_allowed": False,
            "message": "No blind ISO download; operator must start fetch explicitly.",
        }
    return {
        "allowed": True,
        "reason": "operator_started",
        "auto_download_allowed": False,
        "profile_id": profile_id,
        "cache_rel": str(DEFAULT_ISO_CACHE_REL / profile_id),
        "note": "Policy allows starting download; caller still owns network I/O.",
    }
