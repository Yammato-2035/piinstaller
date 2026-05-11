from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_debian_live_build_plan.json"
_MAX_BYTES = 768 * 1024

_ARTIFACT_ROOT = "build/rescue/"


def _emit(
    status: str,
    body: dict[str, Any],
    *,
    wrote: bool,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "rescue_debian_live_build_plan_status": status,
        "rescue_debian_live_build_plan_file_path": _OUT_REL,
        "rescue_debian_live_build_plan": body,
        "rescue_debian_live_build_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_debian_live_build_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_DEBIAN_PLAN")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_DEBIAN_PLAN_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DEBIAN_PLAN")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    packages = {
        "base": [
            "systemd",
            "network-manager",
            "curl",
            "jq",
            "python3",
            "python3-venv",
            "ca-certificates",
        ],
        "storage": [
            "util-linux",
            "smartmontools",
            "parted",
            "gdisk",
            "dosfstools",
            "e2fsprogs",
            "xfsprogs",
            "btrfs-progs",
            "ntfs-3g",
        ],
        "rescue": [
            "rsync",
            "tar",
            "gzip",
            "zstd",
            "cryptsetup",
            "efibootmgr",
            "grub-efi-amd64-bin",
        ],
        "ui": [
            "chromium",
            "xorg",
            "fonts-dejavu-core",
            "setuphelfer-frontend-package-placeholder",
        ],
        "network_help": [
            "openssh-client",
            "openssh-server",
            "avahi-daemon",
        ],
    }

    body: dict[str, Any] = {
        "rescue_debian_live_build_plan_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_stick_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tooling": "live-build",
        "debian_release": "stable",
        "primary_arch": "amd64",
        "later_tracks": ["arm64", "raspberry_pi_separate_image"],
        "execution_policy": "plan_only_no_execution",
        "artifact_output_root": _ARTIFACT_ROOT,
        "output_paths": [
            f"{_ARTIFACT_ROOT}staging/",
            f"{_ARTIFACT_ROOT}cache/",
            f"{_ARTIFACT_ROOT}iso/",
            f"{_ARTIFACT_ROOT}logs/",
        ],
        "services": [
            {"unit": "setuphelfer-backend.service", "scope": "live_system", "notes": "systemd user/session or system unit TBD"},
        ],
        "autostart": [
            "local browser or kiosk to http://127.0.0.1:<backend>/ optional",
            "evidence directory bind-mount or export path under artifact root",
        ],
        "package_groups": packages,
        "openssh_server_default": "disabled",
        "avahi_daemon": "optional",
        "notes": [
            "All ISO and intermediate artifacts must remain under build/rescue/.",
            "No live-build execution from backend runners in this phase.",
        ],
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("ok", body, wrote=True, warnings=[], errors=[])
