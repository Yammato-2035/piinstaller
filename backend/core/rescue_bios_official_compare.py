"""Official BIOS version comparison for ASUS and MSI (read-only).

Sources: official manufacturer catalog entries only (no third-party download portals).
Never downloads or executes firmware. Never flashes.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.parse import urlparse

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1

ALLOWED_HOST_SUFFIXES = (
    "asus.com",
    "www.asus.com",
    "dlcdnets.asus.com",
    "dlcdnet.asus.com",
    "msi.com",
    "www.msi.com",
    "download.msi.com",
    "fwupd.org",  # optional LVFS metadata only
)

# Static official catalog seeds — extended after physical model confirmation.
# Versions are illustrative placeholders until live official lookup populates evidence.
OFFICIAL_BIOS_CATALOG: dict[str, dict[str, Any]] = {
    "msi_ge63_ms16p5": {
        "vendor": "MSI",
        "exact_model": "GE63 Raider RGB 8RF (MS-16P5)",
        "board": "MS-16P5",
        "latest_version": "E16P5IMS.31A",
        "release_date": "2021-07-14",
        "support_url": "https://www.msi.com/Laptop/GE63-Raider-RGB-8RF/support",
        "download_url": "https://www.msi.com/Laptop/GE63-Raider-RGB-8RF/support",
        "checksum_sha256": None,
        "notes": "Use MSI Support only; operator flash via M-Flash later.",
    },
    "asus_rog_gabriel_pending": {
        "vendor": "ASUS",
        "exact_model": "ASUS ROG (Gabriel — exact SKU pending physical identity)",
        "board": "",
        "latest_version": None,
        "release_date": None,
        "support_url": "https://www.asus.com/support/",
        "download_url": None,
        "checksum_sha256": None,
        "notes": "Exact model must be confirmed on hardware before recommending BIOS.",
    },
}


def is_official_source_url(url: str) -> bool:
    if not url:
        return False
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    if not host:
        return False
    for suffix in ALLOWED_HOST_SUFFIXES:
        if host == suffix or host.endswith("." + suffix):
            return True
    return False


def _normalize_bios_token(version: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", (version or "").upper())


def compare_bios_versions(installed: str, latest: str | None) -> str:
    """Compare BIOS labels. Prefer equality; avoid naive numeric sort for alphanumerics."""
    if not latest:
        return "unknown"
    a = _normalize_bios_token(installed)
    b = _normalize_bios_token(latest)
    if not a or not b:
        return "unknown"
    if a == b:
        return "current"
    # MSI/ASUS often use codes like E16P5IMS.31A — if installed contains latest token or vice versa
    if a in b or b in a:
        return "current"
    # Cannot safely decide newer without vendor ordering rules → update_available as recommendation only
    return "update_available"


def resolve_catalog_key(machine: Mapping[str, Any]) -> str | None:
    profile = str(machine.get("expected_profile") or "")
    board = str(machine.get("board_name") or "")
    product = str(machine.get("product_name") or "")
    if profile == "msi_ge63" or "16P5" in board.upper() or "GE63" in product.upper():
        return "msi_ge63_ms16p5"
    if profile == "asus_rog_gabriel":
        return "asus_rog_gabriel_pending"
    return None


def check_latest_official_bios(
    *,
    machine: Mapping[str, Any],
    online: bool = True,
    catalog: Mapping[str, Mapping[str, Any]] | None = None,
    override_installed_version: str | None = None,
) -> dict[str, Any]:
    conf = str(machine.get("confidence") or "low")
    profile = str(machine.get("expected_profile") or "unknown")
    installed = override_installed_version or str(machine.get("bios_version") or "")
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if conf == "low" or profile == "unknown":
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "status": "blocked_model_ambiguous" if conf != "high" and profile != "msi_ge63" else "blocked",
            "vendor": machine.get("manufacturer") or "",
            "exact_model": machine.get("product_name") or "",
            "installed_version": installed,
            "latest_official_version": None,
            "automatic_flash_allowed": False,
            "fetched_at": fetched_at,
            "online": online,
        }

    if not online:
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "status": "latest_version_unknown_offline",
            "vendor": machine.get("manufacturer") or "",
            "exact_model": machine.get("product_name") or "",
            "installed_version": installed,
            "latest_official_version": None,
            "automatic_flash_allowed": False,
            "fetched_at": fetched_at,
            "online": False,
        }

    cat = dict(catalog or OFFICIAL_BIOS_CATALOG)
    key = resolve_catalog_key(machine)
    if not key or key not in cat:
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "status": "blocked_model_ambiguous",
            "vendor": machine.get("manufacturer") or "",
            "exact_model": machine.get("product_name") or "",
            "installed_version": installed,
            "latest_official_version": None,
            "automatic_flash_allowed": False,
            "fetched_at": fetched_at,
            "online": online,
        }

    entry = dict(cat[key])
    support_url = str(entry.get("support_url") or "")
    download_url = str(entry.get("download_url") or "") or None
    if support_url and not is_official_source_url(support_url):
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "status": "blocked",
            "reason": "non_official_source_rejected",
            "automatic_flash_allowed": False,
            "fetched_at": fetched_at,
        }
    if download_url and not is_official_source_url(download_url):
        download_url = None

    latest = entry.get("latest_version")
    if latest is None and key.startswith("asus_"):
        cmp_status = "unknown"
    else:
        cmp_status = compare_bios_versions(installed, str(latest) if latest else None)

    plan = None
    if cmp_status == "update_available":
        plan = build_bios_update_plan(
            vendor=str(entry.get("vendor") or ""),
            support_url=support_url,
            recommended_method="msi_m_flash" if "msi" in key else "asus_ez_flash",
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "status": cmp_status,
        "vendor": entry.get("vendor"),
        "exact_model": entry.get("exact_model"),
        "board": entry.get("board"),
        "installed_version": installed,
        "latest_official_version": latest,
        "release_date": entry.get("release_date"),
        "official_support_url": support_url,
        "download_url": download_url,
        "checksum_sha256": entry.get("checksum_sha256"),
        "changelog": entry.get("notes"),
        "fetched_at": fetched_at,
        "online": online,
        "automatic_flash_allowed": False,
        "update_plan": plan,
        "end_state": "bios_checked",
    }


def build_bios_update_plan(
    *,
    vendor: str,
    support_url: str,
    recommended_method: str,
) -> dict[str, Any]:
    return {
        "status": "update_available",
        "automatic_flash_allowed": False,
        "recommended_method": recommended_method,
        "requirements": [
            "official firmware file",
            "AC power connected",
            "battery above required threshold",
            "exact machine model confirmed",
            "separate operator approval",
        ],
        "warnings": [
            "Check BitLocker/device encryption recovery key if Windows present",
            "Review Secure Boot/TPM impact before flashing",
        ],
        "official_source": support_url,
        "vendor": vendor,
    }
