"""RS-P2A WiFi runtime contract — ensure_managed before scan."""

from __future__ import annotations

CONTRACT_VERSION = 1

REQUIRED_BOOT_STEPS = (
    "rfkill_check",
    "networkmanager_check",
    "ensure_managed",
    "nmcli_radio_wifi_on",
    "rescan",
)


def wifi_runtime_preflight_steps() -> list[str]:
    return list(REQUIRED_BOOT_STEPS)


def classify_wifi_runtime_blockers(
    *,
    wifi_status: dict,
    target_mode: str = "external_hdd",
) -> dict:
    blocks_hdd = bool(wifi_status.get("blocks_local_hdd_backup"))
    blocks_cloud = bool(wifi_status.get("blocks_cloud_backup"))
    errors = list(wifi_status.get("errors") or [])
    if target_mode == "cloud_pro" and blocks_cloud:
        errors.append({"code": "blocked_cloud_selected_but_wifi_missing", "message": "Cloud ohne WLAN blockiert."})
    return {
        "contract_version": CONTRACT_VERSION,
        "ensure_managed_before_scan": True,
        "blocks_local_hdd_backup": blocks_hdd,
        "blocks_cloud_backup": blocks_cloud,
        "warnings": [] if not blocks_hdd or target_mode != "external_hdd" else [
            {"code": "wifi_missing_hdd_ok", "message": "WLAN fehlt — lokales HDD-Backup nicht blockiert."}
        ],
        "errors": errors,
        "execute_allowed": False,
    }
