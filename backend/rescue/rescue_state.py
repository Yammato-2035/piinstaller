"""Rescue state aggregation — boot status + spool + machine profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from rescue.rescue_boot_status import (
    build_rescue_boot_status,
    medium_status_from_checks,
    network_is_boot_blocker,
    telemetry_is_boot_blocker,
)
from rescue.rescue_evidence_spool import build_spool_layout_manifest, resolve_spool_base
from rescue.rescue_machine_profile import build_machine_profile, load_machine_profile


def build_rescue_state_snapshot(
    *,
    squashfs_hash_ok: bool | None = None,
    evidence_ok: bool | None = None,
    network_status: str = "not_configured",
    telemetry_status: str = "disabled",
    ui_mode: str = "react",
    ui_status: str = "starting",
    esp_mount: Path | None = None,
    machine_profile_path: Path | None = None,
    rs001_ready: bool = False,
) -> dict[str, Any]:
    medium_status = medium_status_from_checks(
        squashfs_hash_ok=squashfs_hash_ok,
        evidence_ok=evidence_ok,
    )
    boot_status = build_rescue_boot_status(
        medium={
            "status": medium_status,
            "squashfs_hash_ok": squashfs_hash_ok,
            "evidence_ok": evidence_ok,
            "required": True,
        },
        network={
            "status": network_status,
            "required": False,
            "wifi_scan_started": False,
        },
        telemetry={
            "status": telemetry_status,
            "required": False,
            "opt_in": telemetry_status not in ("disabled", "skipped"),
        },
        ui={
            "mode": ui_mode,
            "status": ui_status,
            "shows_systemd_failures": False,
        },
        rs001={
            "status": "yellow",
            "reason": "hardware retest pending",
            "ready_for_operator_retest": rs001_ready,
        },
    )
    spool_base = resolve_spool_base(esp_mount=esp_mount)
    profile_path = machine_profile_path or (spool_base / "setuphelfer/profiles/machines/current.json")
    profile = load_machine_profile(profile_path) or build_machine_profile()
    return {
        "schema_version": 1,
        "boot_status": boot_status,
        "spool": build_spool_layout_manifest(spool_base),
        "machine_profile": profile,
        "offline_first": {
            "network_blocks_boot": network_is_boot_blocker(boot_status["network"]),
            "telemetry_blocks_boot": telemetry_is_boot_blocker(boot_status["telemetry"]),
        },
        "secrets_exposed": False,
    }
