from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import (
    BUILD_RESCUE_ROOT,
    REPO_ROOT,
    ensure_rescue_workspace_dirs,
    guard_handoff_overwrite,
    resolve_handoff_path,
    write_json_handoff,
)

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_live_build_config.json"
_MAX_BYTES = 768 * 1024


def _emit(status: str, body: dict[str, Any], *, out_rel: str, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_live_build_config_status": status,
        "rescue_live_build_config_file_path": out_rel,
        "rescue_live_build_config": body,
        "rescue_live_build_config_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_live_build_config(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    """Generates Debian live-build configuration manifest (JSON only; no lb execution)."""
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_LBCFG")
    if oerr or out_path is None:
        return _emit("blocked", {}, out_rel=_OUT_REL, wrote=False, warnings=[], errors=[oerr or "RESCUE_LBCFG_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_LBCFG")
    if gerr:
        return _emit("blocked", {}, out_rel=_OUT_REL, wrote=False, warnings=[], errors=[gerr])

    ensure_rescue_workspace_dirs()
    cfg_version: dict[str, Any] = {}
    vpath = REPO_ROOT / "config" / "version.json"
    try:
        if vpath.is_file():
            raw = json.loads(vpath.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                cfg_version = raw
    except OSError:
        pass

    evidence_dir = str((BUILD_RESCUE_ROOT / "evidence").relative_to(REPO_ROOT)).replace("\\", "/")

    body: dict[str, Any] = {
        "rescue_live_build_config_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_iso_phase1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "execution_mode": "config_only_no_build",
        "debian": {"release": "stable", "arch": "amd64", "live_build_tooling": "live-build"},
        "hostname": "setuphelfer-rescue-live",
        "live_user": {"name": "user", "fullname": "Setuphelfer Rescue", "sudo_nopasswd": True},
        "live_boot": {"persistence": "none_default", "readonly_overlay": True, "rescue_mode_flag": True},
        "package_lists": {
            "base": ["systemd", "network-manager", "curl", "jq", "python3", "python3-venv", "ca-certificates"],
            "storage": ["util-linux", "smartmontools", "parted", "gdisk", "dosfstools", "e2fsprogs"],
            "ui": ["chromium", "xorg", "openbox", "fonts-dejavu-core"],
        },
        "setuphelfer_services": [
            {
                "unit": "setuphelfer-backend.service",
                "description": "Bind to 127.0.0.1 in live; drop-in under /etc/systemd/system",
                "after": ["network-online.target"],
            }
        ],
        "autostart": [
            {"type": "xdg_autostart", "exec": "chromium --kiosk http://127.0.0.1:8000/", "optional": True},
            {"type": "systemd_user", "exec": "optional", "optional": True},
        ],
        "browser_ui": {"default_url": "http://127.0.0.1:8000/", "kiosk": True},
        "workspace": {
            "live_build_dir": "build/rescue/live-build/",
            "iso_output_dir": "build/rescue/output/",
            "logs_dir": "build/rescue/logs/",
            "evidence_dir": evidence_dir,
        },
        "readonly_rescue_mode": True,
        "evidence_directory": evidence_dir,
        "project_version_hint": str(cfg_version.get("project_version") or ""),
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, out_rel=_OUT_REL, wrote=False, warnings=[], errors=[werr])
    return _emit("ok", body, out_rel=_OUT_REL, wrote=True, warnings=[], errors=[])
