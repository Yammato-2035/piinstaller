"""PI-RS-PAYLOAD-TELEMETRY-001 — read-only squashfs content checks for lab telemetry."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.rescue_payload_version import rescue_payload_version

_LAB_MODULE_MARKERS = (
    "rescue_stick_cloud_lab_models.py",
    "rescue_stick_cloud_lab_config.py",
    "rescue_stick_cloud_lab_payload.py",
    "rescue_stick_cloud_lab_send.py",
)

_LAB_SCRIPT_MARKERS = (
    "lab-rs-tel-send001-preview.sh",
    "lab-rs-tel-send001-send.sh",
)

_SECRET_MARKERS = (
    "telemetry-lab-token",
    "telemetry-lab-hmac-key",
    "Authorization: Bearer",
    "X-API-Key:",
)


def _unsquashfs_listing(squashfs_path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["unsquashfs", "-ll", str(squashfs_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    blob = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, blob


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


def default_repacked_squashfs_path(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    version = rescue_payload_version()
    return root / "build" / "rescue" / f"filesystem.squashfs.repacked-{version}"


def verify_rescue_payload_telemetry_content(squashfs_path: Path) -> dict[str, Any]:
    ok, listing = _unsquashfs_listing(squashfs_path)
    version_file = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/VERSION").strip()
    expected_version = rescue_payload_version()

    modules = {name: name in listing for name in _LAB_MODULE_MARKERS}
    scripts = {name: name in listing for name in _LAB_SCRIPT_MARKERS}
    secret_hits = [marker for marker in _SECRET_MARKERS if marker in listing]

    return {
        "squashfs_path": str(squashfs_path),
        "unsquashfs_ok": ok,
        "version_expected": expected_version,
        "version_in_payload": version_file,
        "version_match": version_file == expected_version,
        "lab_modules": modules,
        "lab_modules_present": all(modules.values()),
        "lab_scripts": scripts,
        "lab_scripts_present": all(scripts.values()),
        "secret_markers_in_listing": secret_hits,
        "secrets_absent": not secret_hits,
        "content_ok": ok
        and version_file == expected_version
        and all(modules.values())
        and all(scripts.values())
        and not secret_hits,
    }
