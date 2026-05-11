from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_PLATFORMS = {"linux-x86_64", "raspberrypi-arm64", "raspberrypi-armhf"}
_ARCHS = {"x86_64", "arm64", "armhf", "unknown"}
_LOCAL_EXTS = {".img", ".iso", ".qcow2"}


def get_deploy_source_registry() -> dict[str, Any]:
    return {
        "registry_version": 1,
        "sources": [
            {
                "source_id": "SRC_UBUNTU_SERVER_LTS",
                "type": "official_installer",
                "name": "ubuntu-server-lts",
                "vendor": "canonical",
                "architecture": "x86_64",
                "platforms": ["linux-x86_64", "raspberrypi-arm64"],
                "supported_profiles": ["DEPLOY_PROFILE_MINIMAL_LINUX", "DEPLOY_PROFILE_WEB_SERVER", "DEPLOY_PROFILE_BACKUP_NODE"],
                "requires_network": False,
                "requires_download": False,
                "checksum_required": True,
                "status": "metadata_only",
                "risk_level": "medium",
                "local_path": "",
                "remote_url": "",
                "checksum": "",
                "warnings": [],
                "errors": [],
            },
            {
                "source_id": "SRC_DEBIAN_MINIMAL",
                "type": "official_installer",
                "name": "debian-minimal",
                "vendor": "debian",
                "architecture": "x86_64",
                "platforms": ["linux-x86_64", "raspberrypi-arm64"],
                "supported_profiles": ["DEPLOY_PROFILE_MINIMAL_LINUX", "DEPLOY_PROFILE_WEB_SERVER", "DEPLOY_PROFILE_BACKUP_NODE"],
                "requires_network": False,
                "requires_download": False,
                "checksum_required": True,
                "status": "metadata_only",
                "risk_level": "low",
                "local_path": "",
                "remote_url": "",
                "checksum": "",
                "warnings": [],
                "errors": [],
            },
            {
                "source_id": "SRC_RPI_OS_LITE",
                "type": "official_installer",
                "name": "raspberry-pi-os-lite",
                "vendor": "raspberrypi",
                "architecture": "arm64",
                "platforms": ["raspberrypi-arm64", "raspberrypi-armhf"],
                "supported_profiles": ["DEPLOY_PROFILE_MINIMAL_LINUX", "DEPLOY_PROFILE_NAS"],
                "requires_network": False,
                "requires_download": False,
                "checksum_required": True,
                "status": "metadata_only",
                "risk_level": "low",
                "local_path": "",
                "remote_url": "",
                "checksum": "",
                "warnings": [],
                "errors": [],
            },
            {
                "source_id": "SRC_RPI_OS_DESKTOP",
                "type": "official_installer",
                "name": "raspberry-pi-os-desktop",
                "vendor": "raspberrypi",
                "architecture": "arm64",
                "platforms": ["raspberrypi-arm64", "raspberrypi-armhf"],
                "supported_profiles": ["DEPLOY_PROFILE_MINIMAL_LINUX", "DEPLOY_PROFILE_EXPERIMENTAL"],
                "requires_network": False,
                "requires_download": False,
                "checksum_required": True,
                "status": "metadata_only",
                "risk_level": "medium",
                "local_path": "",
                "remote_url": "",
                "checksum": "",
                "warnings": [],
                "errors": [],
            },
            {
                "source_id": "SRC_SETUPHELFER_RECOVERY_MINIMAL",
                "type": "local_image",
                "name": "setuphelfer-recovery-minimal",
                "vendor": "setuphelfer",
                "architecture": "unknown",
                "platforms": ["linux-x86_64", "raspberrypi-arm64", "raspberrypi-armhf"],
                "supported_profiles": ["DEPLOY_PROFILE_MINIMAL_LINUX", "DEPLOY_PROFILE_BACKUP_NODE"],
                "requires_network": False,
                "requires_download": False,
                "checksum_required": False,
                "status": "available",
                "risk_level": "low",
                "local_path": "",
                "remote_url": "",
                "checksum": "",
                "warnings": [],
                "errors": [],
            },
            {
                "source_id": "SRC_EXPERIMENTAL_GENERIC_LINUX",
                "type": "remote_image",
                "name": "experimental-generic-linux",
                "vendor": "community",
                "architecture": "unknown",
                "platforms": ["linux-x86_64", "raspberrypi-arm64"],
                "supported_profiles": ["DEPLOY_PROFILE_EXPERIMENTAL"],
                "requires_network": True,
                "requires_download": True,
                "checksum_required": True,
                "status": "experimental",
                "risk_level": "high",
                "local_path": "",
                "remote_url": "",
                "checksum": "",
                "warnings": ["DEPLOY_SOURCE_REMOTE_DOWNLOAD_BLOCKED"],
                "errors": [],
            },
        ],
    }


def _host_platform(inspect_result: dict[str, Any]) -> str:
    sys_d = inspect_result.get("system") if isinstance(inspect_result.get("system"), dict) else {}
    machine = str(sys_d.get("machine") or sys_d.get("architecture") or "").lower()
    if machine in {"x86_64", "amd64"}:
        return "linux-x86_64"
    if machine in {"aarch64", "arm64"}:
        return "raspberrypi-arm64"
    if machine.startswith("arm"):
        return "raspberrypi-armhf"
    return "linux-x86_64"


def evaluate_source_compatibility(source: dict, inspect_result: dict, deploy_plan: dict) -> dict:
    warnings: list[str] = []
    errors: list[str] = []
    reasons: list[str] = []

    platform = _host_platform(inspect_result if isinstance(inspect_result, dict) else {})
    source_platforms = source.get("platforms") if isinstance(source.get("platforms"), list) else []
    source_profiles = source.get("supported_profiles") if isinstance(source.get("supported_profiles"), list) else []
    rec = deploy_plan.get("recommended_profile") if isinstance(deploy_plan.get("recommended_profile"), dict) else {}
    rec_code = str(rec.get("code") or "")

    if source.get("status") == "blocked":
        errors.append("DEPLOY_SOURCE_STATUS_BLOCKED")
        reasons.append("status_blocked")
    if source.get("status") == "experimental":
        warnings.append("DEPLOY_SOURCE_EXPERIMENTAL")
        reasons.append("experimental_source")
    if platform not in source_platforms:
        errors.append("DEPLOY_SOURCE_PLATFORM_MISMATCH")
        reasons.append("platform_mismatch")
    if rec_code and rec_code not in source_profiles:
        errors.append("DEPLOY_SOURCE_PROFILE_MISMATCH")
        reasons.append("profile_mismatch")

    hw = deploy_plan.get("hardware_summary") if isinstance(deploy_plan.get("hardware_summary"), dict) else {}
    net_available = hw.get("network_available")
    if bool(source.get("requires_network")) and net_available is False:
        errors.append("DEPLOY_SOURCE_NETWORK_REQUIRED")
        reasons.append("network_missing")

    risk = str(source.get("risk_level") or "medium")
    if source.get("status") == "experimental":
        risk = "high"

    return {
        "compatible": len(errors) == 0,
        "risk_level": risk if risk in {"low", "medium", "high"} else "medium",
        "warnings": warnings,
        "errors": errors,
        "reasons": reasons,
    }


def validate_local_image_entry(source: dict) -> dict[str, Any]:
    p = str(source.get("local_path") or "")
    if not p:
        return {"code": "DEPLOY_SOURCE_LOCAL_IMAGE_MISSING"}
    path = Path(p)
    if not path.exists():
        return {"code": "DEPLOY_SOURCE_LOCAL_IMAGE_MISSING"}
    if not path.is_file():
        return {"code": "DEPLOY_SOURCE_LOCAL_IMAGE_INVALID"}
    if path.suffix.lower() not in _LOCAL_EXTS:
        return {"code": "DEPLOY_SOURCE_LOCAL_IMAGE_INVALID"}
    return {"code": "DEPLOY_SOURCE_LOCAL_IMAGE_VALID"}


def validate_remote_image_metadata(source: dict) -> dict[str, Any]:
    url = str(source.get("remote_url") or source.get("url") or "")
    checksum = str(source.get("checksum") or "")
    if not url:
        return {"code": "DEPLOY_SOURCE_REMOTE_METADATA_INVALID"}
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        return {"code": "DEPLOY_SOURCE_REMOTE_METADATA_INVALID"}
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local") or host.endswith(".internal"):
        return {"code": "DEPLOY_SOURCE_REMOTE_METADATA_INVALID"}
    if not checksum:
        return {"code": "DEPLOY_SOURCE_REMOTE_METADATA_INVALID"}
    return {"code": "DEPLOY_SOURCE_REMOTE_METADATA_VALID", "warning": "DEPLOY_SOURCE_REMOTE_DOWNLOAD_BLOCKED"}
