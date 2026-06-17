"""Rescue backup plan-only API handlers (RS-F2S)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.rescue_backup_target_policy import rescue_backup_preflight, rescue_capabilities_matrix
from core.rescue_cloud_target_local import cloud_target_status, save_cloud_target_config
from core.rescue_storage_discovery import discover_rescue_storage
from rescue.boot_context import build_rescue_boot_context


def _booted_from_rescue() -> bool:
    try:
        ctx = build_rescue_boot_context()
        boot = ctx.get("boot_context") if isinstance(ctx.get("boot_context"), dict) else {}
        return bool(boot.get("booted_from_rescue") or boot.get("rescue_medium_detected"))
    except Exception:
        return Path("/run/live/medium").is_dir()


async def get_rescue_capabilities() -> dict[str, Any]:
    base = rescue_capabilities_matrix()
    base["booted_from_rescue"] = _booted_from_rescue()
    base["cloud_target"] = {
        "local_unlock_test": True,
        "public_repo_implementation": False,
        "status": cloud_target_status(),
    }
    base["endpoints"] = {
        "backup_execute": base["booted_from_rescue"],
        "restore_execute": False,
        "restore_preview": True,
        "wipe": False,
        "linux_install": False,
    }
    return base


async def get_storage_discovery() -> dict[str, Any]:
    return discover_rescue_storage()


async def post_cloud_target_local(body: dict[str, Any]) -> dict[str, Any]:
    return save_cloud_target_config(
        endpoint=str(body.get("endpoint") or ""),
        username=str(body.get("username") or ""),
        password=str(body.get("password") or ""),
        bucket=str(body.get("bucket") or ""),
        enabled=bool(body.get("enabled", True)),
    )


async def get_cloud_target_local_status() -> dict[str, Any]:
    return cloud_target_status()


async def post_backup_preflight(body: dict[str, Any]) -> dict[str, Any]:
    return rescue_backup_preflight(
        source_device=str(body.get("source_device") or ""),
        source_size_bytes=int(body.get("source_size_bytes") or 0),
        target_mount=str(body.get("target_mount") or ""),
        target_device=str(body.get("target_device") or ""),
        free_bytes=int(body.get("free_bytes") or 0),
        fstype=str(body.get("fstype") or ""),
        operator_confirmation_1=body.get("operator_confirmation_1"),
        operator_confirmation_2=body.get("operator_confirmation_2"),
    )


async def post_backup_plan(body: dict[str, Any]) -> dict[str, Any]:
    from core.rescue_backup_plan_contract import build_rescue_backup_plan

    return build_rescue_backup_plan(body)


async def post_full_backup_plan(body: dict[str, Any]) -> dict[str, Any]:
    from core.rescue_backup_plan_contract import build_rescue_full_backup_plan

    return build_rescue_full_backup_plan(body)


async def get_system_summary() -> dict[str, Any]:
    from core.rescue_system_identity import build_rescue_system_summary

    return build_rescue_system_summary()
