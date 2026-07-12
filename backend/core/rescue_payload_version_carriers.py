"""PI-RS-MSI-GUI-003 — synchronized rescue payload version carriers."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_payload_version import previous_rescue_payload_version, rescue_payload_version

_ACTIVE_RUNTIME_PATHS = (
    "opt/setuphelfer-rescue/VERSION",
    "opt/setuphelfer-rescue/config/rescue_payload_version.json",
    "opt/setuphelfer-rescue/config/version.json",
)


def build_rescue_runtime_version_json(payload_version: str | None = None) -> dict[str, Any]:
    version = (payload_version or rescue_payload_version()).strip()
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_version": version,
        "release_stage": "internal_testing",
        "schema_version": 1,
        "version_source_of_truth": True,
        "version_track": "rescue_payload_sync",
        "rescue_payload_version": version,
    }


def build_rescue_payload_version_json(payload_version: str | None = None) -> dict[str, Any]:
    version = (payload_version or rescue_payload_version()).strip()
    previous = previous_rescue_payload_version()
    return {
        "schema_version": 1,
        "rescue_payload_version": version,
        "previous_rescue_payload_version": previous,
        "pi_rs_msi_gui_003": True,
        "version_source_of_truth": True,
    }


def _unsquashfs_cat(squashfs_path: Path, member: str) -> str:
    proc = subprocess.run(
        ["unsquashfs", "-force", "-no-xattrs", "-cat", str(squashfs_path), member],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def read_payload_version_carriers(squashfs_path: Path) -> dict[str, Any]:
    carriers: dict[str, Any] = {}
    version_file = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/VERSION").strip()
    carriers["VERSION"] = version_file
    payload_cfg_raw = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/config/rescue_payload_version.json")
    if payload_cfg_raw.strip():
        payload_cfg = json.loads(payload_cfg_raw)
        carriers["rescue_payload_version.json"] = str(payload_cfg.get("rescue_payload_version") or "")
    else:
        carriers["rescue_payload_version.json"] = ""
    version_json_raw = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/config/version.json")
    if version_json_raw.strip():
        version_json = json.loads(version_json_raw)
        carriers["version.json"] = str(version_json.get("project_version") or "")
    else:
        carriers["version.json"] = ""
    return carriers


def verify_payload_version_carriers(
    squashfs_path: Path,
    *,
    expected_version: str | None = None,
) -> dict[str, Any]:
    expected = (expected_version or rescue_payload_version()).strip()
    carriers = read_payload_version_carriers(squashfs_path)
    mismatches = {
        name: value
        for name, value in carriers.items()
        if str(value).strip() != expected
    }
    stale_hits: list[str] = []
    for member in _ACTIVE_RUNTIME_PATHS:
        blob = _unsquashfs_cat(squashfs_path, member)
        if "1.10.0.12" in blob:
            stale_hits.append(member)
    return {
        "payload_version_expected": expected,
        "payload_version_carriers": carriers,
        "all_version_carriers_match": not mismatches and not stale_hits,
        "mismatches": mismatches,
        "stale_runtime_version_hits": stale_hits,
    }
