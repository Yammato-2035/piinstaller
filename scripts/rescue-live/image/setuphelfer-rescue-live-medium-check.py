#!/usr/bin/env python3
"""Live-medium stability evaluation for Setuphelfer rescue (ISO hybrid + FAT32 ESP)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

FAT_VOLUME_LABEL = "SETUPHELFER"
GPT_PARTITION_NAME = "SETUPHELFER_RESCUE"
WRITER_MODE_FAT32_ESP = "fat32_esp"

REQUIRED_MEDIUM_PATHS: tuple[str, ...] = (
    "EFI/BOOT/BOOTX64.EFI",
    "boot/grub/grub.cfg",
    "live/vmlinuz",
    "live/initrd.img",
    "live/filesystem.squashfs",
    "setuphelfer/rescue/evidence.json",
    "setuphelfer/rescue/version.json",
    "setuphelfer/rescue/boot-branding.txt",
)

SQUASHFS_SPOT_PATHS: tuple[str, ...] = (
    "usr/bin/nmcli",
    "usr/bin/curl",
    "usr/local/sbin/setuphelfer-rescue-telemetry-push",
    "usr/local/sbin/setuphelfer-rescue-telemetry-build-payload.py",
    "usr/local/sbin/setuphelfer-rescue-network-onboarding",
    "usr/local/sbin/setuphelfer-rescue-start-assistant",
    "usr/share/setuphelfer/rescue/boot-branding.txt",
)

SQUASHFS_DIRECT_CANDIDATES: tuple[str, ...] = (
    "/run/live/medium/live/filesystem.squashfs",
    "/lib/live/mount/medium/live/filesystem.squashfs",
)

MEDIUM_ROOT_CANDIDATES: tuple[str, ...] = (
    "/run/live/medium",
    "/lib/live/mount/medium",
)

Runner = Callable[..., Any]


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_rescue_live(proc_cmdline: str | None = None) -> bool:
    if Path("/run/live/medium").is_dir():
        return True
    cmdline = proc_cmdline
    if cmdline is None:
        try:
            cmdline = Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
        except OSError:
            cmdline = ""
    return "setuphelfer_rescue=1" in cmdline or "boot=live" in cmdline


def _glob_medium_roots() -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()
    for base in MEDIUM_ROOT_CANDIDATES:
        p = Path(base)
        if p.is_dir():
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                roots.append(p)
    media = Path("/media")
    if media.is_dir():
        for child in sorted(media.iterdir()):
            if not child.is_dir():
                continue
            label = child.name.upper()
            if label in {FAT_VOLUME_LABEL, GPT_PARTITION_NAME}:
                key = str(child.resolve())
                if key not in seen:
                    seen.add(key)
                    roots.append(child)
    return roots


def resolve_squashfs_and_medium_root(
    *,
    medium_roots: Sequence[Path] | None = None,
    path_exists: Callable[[Path], bool] | None = None,
) -> tuple[Path | None, Path | None]:
    exists = path_exists or (lambda p: p.is_file())
    roots = list(medium_roots or _glob_medium_roots())
    for root in roots:
        candidate = root / "live/filesystem.squashfs"
        if exists(candidate):
            return candidate, root
    for direct in SQUASHFS_DIRECT_CANDIDATES:
        candidate = Path(direct)
        if exists(candidate):
            medium_root = candidate.parent.parent
            return candidate, medium_root
    return None, None


def load_medium_evidence(medium_root: Path) -> dict[str, Any]:
    path = medium_root / "setuphelfer/rescue/evidence.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def detect_medium_mode(
    medium_root: Path | None,
    evidence: Mapping[str, Any],
) -> str:
    if evidence.get("writer_mode") == WRITER_MODE_FAT32_ESP:
        return "fat32_esp"
    if medium_root is not None:
        ev_path = medium_root / "setuphelfer/rescue/evidence.json"
        if ev_path.is_file():
            return "fat32_esp"
        if (medium_root / "live/filesystem.squashfs").is_file():
            return "iso_hybrid"
    return "unknown"


def squashfs_expected_sha256(evidence: Mapping[str, Any]) -> str | None:
    for entry in evidence.get("files") or []:
        if entry.get("staging_path") == "live/filesystem.squashfs":
            sha = entry.get("sha256")
            if isinstance(sha, str) and sha.strip():
                return sha.strip().lower()
    return None


def required_medium_files_present(
    medium_root: Path | None,
    *,
    path_exists: Callable[[Path], bool] | None = None,
) -> tuple[bool, list[str]]:
    if medium_root is None:
        return False, list(REQUIRED_MEDIUM_PATHS)
    exists = path_exists or (lambda p: p.is_file())
    missing = [rel for rel in REQUIRED_MEDIUM_PATHS if not exists(medium_root / rel)]
    return not missing, missing


def read_squashfs_ok(
    squashfs_path: Path,
    *,
    reader: Callable[[Path], bool] | None = None,
) -> bool:
    if reader is not None:
        return reader(squashfs_path)
    try:
        with squashfs_path.open("rb") as handle:
            while handle.read(4 * 1024 * 1024):
                pass
        return True
    except OSError:
        return False


def squashfs_spot_checks_ok(
    squashfs_path: Path,
    *,
    spot_reader: Callable[[Path, str], bool] | None = None,
) -> tuple[bool, list[str]]:
    failed: list[str] = []

    def _default_spot(sq: Path, inner: str) -> bool:
        try:
            proc = subprocess.run(
                ["unsquashfs", "-cat", str(sq), inner],
                capture_output=True,
                timeout=120,
                check=False,
            )
            return proc.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    spot = spot_reader or _default_spot
    for inner in SQUASHFS_SPOT_PATHS:
        if not spot(squashfs_path, inner):
            failed.append(inner)
    return not failed, failed


def sha256_file(path: Path, *, hasher: Callable[[bytes], None] | None = None) -> str:
    h = hashlib.sha256()

    def _default(chunk: bytes) -> None:
        h.update(chunk)

    feed = hasher or _default
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            feed(chunk)
    return h.hexdigest()


def evaluate_live_medium_check(
    *,
    proc_cmdline: str | None = None,
    medium_roots: Sequence[Path] | None = None,
    path_exists: Callable[[Path], bool] | None = None,
    squashfs_reader: Callable[[Path], bool] | None = None,
    spot_reader: Callable[[Path, str], bool] | None = None,
    sha256_fn: Callable[[Path], str] | None = None,
) -> dict[str, Any]:
    """Pure evaluation — unit-testable without real mounts."""
    error_code: str | None = None
    live_stable = False
    read_ok = False
    spot_ok = True
    spot_failed: list[str] = []
    evidence_status = "complete"
    hash_ok: bool | None = None
    expected_sha: str | None = None
    actual_sha: str | None = None
    missing_files: list[str] = []

    if not _is_rescue_live(proc_cmdline):
        return {
            "checked_at": _now_iso(),
            "squashfs_path": None,
            "medium_root": None,
            "medium_mode": "unknown",
            "squashfs_read_ok": False,
            "spot_checks_ok": False,
            "spot_check_failures": [],
            "required_files_ok": False,
            "required_files_missing": list(REQUIRED_MEDIUM_PATHS),
            "squashfs_hash_ok": None,
            "expected_squashfs_sha256": None,
            "actual_squashfs_sha256": None,
            "live_media_runtime_stable": False,
            "evidence_status": "review_required",
            "operator_hints": ["toram_boot_recommended", "usb_rewrite_recommended", "no_repair_or_install"],
            "error_code": "NOT_RESCUE_LIVE",
            "secrets_exposed": False,
        }

    squashfs_path, medium_root = resolve_squashfs_and_medium_root(
        medium_roots=medium_roots,
        path_exists=path_exists,
    )
    evidence = load_medium_evidence(medium_root) if medium_root else {}
    medium_mode = detect_medium_mode(medium_root, evidence)

    if squashfs_path is None:
        error_code = "SQUASHFS_PATH_MISSING"
    else:
        read_ok = read_squashfs_ok(squashfs_path, reader=squashfs_reader)
        if not read_ok:
            error_code = "SQUASHFS_READ_IO_ERROR"
        else:
            spot_ok, spot_failed = squashfs_spot_checks_ok(squashfs_path, spot_reader=spot_reader)
            if not spot_ok:
                error_code = "SQUASHFS_SPOT_CHECK_FAILED"

    req_ok, missing_files = required_medium_files_present(medium_root, path_exists=path_exists)

    if medium_mode == "fat32_esp":
        if not req_ok:
            error_code = error_code or "FAT32_ESP_REQUIRED_FILES_MISSING"
            evidence_status = "review_required"
        expected_sha = squashfs_expected_sha256(evidence)
        if expected_sha and squashfs_path is not None and read_ok:
            try:
                actual_sha = (sha256_fn or sha256_file)(squashfs_path)
                hash_ok = actual_sha.lower() == expected_sha.lower()
                if not hash_ok:
                    error_code = "FAT32_ESP_SQUASHFS_HASH_MISMATCH"
                    evidence_status = "review_required"
            except OSError:
                hash_ok = False
                error_code = error_code or "FAT32_ESP_SQUASHFS_HASH_ERROR"
                evidence_status = "review_required"
        elif not expected_sha:
            evidence_status = "review_required"
            error_code = error_code or "FAT32_ESP_EVIDENCE_HASH_MISSING"
    elif medium_mode == "iso_hybrid" or medium_root is not None:
        # ISO hybrid / legacy live-boot: squashfs read/spot only on medium surface.
        req_ok = True
        missing_files = []

    if (
        read_ok
        and spot_ok
        and req_ok
        and error_code is None
        and (medium_mode != "fat32_esp" or hash_ok is True)
    ):
        live_stable = True
        evidence_status = "complete"
        error_code = None
    else:
        live_stable = False

    hints: list[str] = []
    if not live_stable:
        hints = ["toram_boot_recommended", "usb_rewrite_recommended", "no_repair_or_install"]

    return {
        "checked_at": _now_iso(),
        "squashfs_path": str(squashfs_path) if squashfs_path else None,
        "medium_root": str(medium_root) if medium_root else None,
        "medium_mode": medium_mode,
        "squashfs_read_ok": read_ok,
        "spot_checks_ok": spot_ok,
        "spot_check_failures": spot_failed,
        "required_files_ok": req_ok,
        "required_files_missing": missing_files,
        "squashfs_hash_ok": hash_ok,
        "expected_squashfs_sha256": expected_sha,
        "actual_squashfs_sha256": actual_sha,
        "live_media_runtime_stable": live_stable,
        "evidence_status": evidence_status,
        "operator_hints": hints,
        "error_code": error_code,
        "secrets_exposed": False,
    }


def main() -> int:
    state_dir = Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))
    out_run = state_dir / "media-check.json"
    out_tmp = Path("/tmp/setuphelfer-rescue-media-check.json")
    state_dir.mkdir(parents=True, exist_ok=True)

    result = evaluate_live_medium_check()
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    out_run.write_text(payload, encoding="utf-8")
    try:
        out_tmp.write_text(payload, encoding="utf-8")
    except OSError:
        pass
    return 0 if result.get("live_media_runtime_stable") else 16


if __name__ == "__main__":
    sys.exit(main())
