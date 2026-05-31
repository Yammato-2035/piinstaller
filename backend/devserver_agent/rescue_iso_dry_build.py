"""Rescue Developer ISO dry-build manifest (no real ISO, chroot, or live-build)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devserver_agent.rescue_profile import (
    validate_developer_profile,
    validate_public_profile_guard,
)

FORBIDDEN_BUILD_TOKENS = frozenset({
    "lb build",
    "debootstrap",
    "chroot",
    "mksquashfs",
    "xorriso",
    "grub-mkrescue",
    "dd",
    "mkfs",
    "mount",
    "umount",
})

FORBIDDEN_ARTIFACT_SUFFIXES = (
    ".iso",
    ".img",
    ".qcow2",
)

FORBIDDEN_ARTIFACT_NAMES = frozenset({
    "filesystem.squashfs",
})

PRIOR_ARTIFACT_MARKERS = (
    "live-build",
    "binary.hybrid.iso",
)

ISO_DRY_BUILD_SOURCE_FORBIDDEN = re.compile(
    r"\b(lb build|debootstrap|chroot|mksquashfs|xorriso|grub-mkrescue)\b",
    re.I,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def build_agent_profile_placement_plan(developer_profile_root: str | Path) -> dict[str, Any]:
    root = Path(developer_profile_root).resolve()
    env_src = root / "environment" / "setuphelfer-dev-agent.env"
    svc_src = root / "systemd" / "setuphelfer-dev-agent.service"
    return {
        "environment_target": "/etc/setuphelfer/setuphelfer-dev-agent.env",
        "systemd_target": "/etc/systemd/system/setuphelfer-dev-agent.service",
        "spool_target": "/opt/setuphelfer/docs/evidence/runtime-results/dev-agent-spool",
        "runtime_module_required": "backend.devserver_agent",
        "source_environment": str(env_src) if env_src.is_file() else None,
        "source_systemd": str(svc_src) if svc_src.is_file() else None,
        "packaging_systemd_reference": "packaging/systemd/setuphelfer-dev-agent.service",
    }


def _artifact_classification(path: Path) -> str:
    rel = str(path).replace("\\", "/")
    for marker in PRIOR_ARTIFACT_MARKERS:
        if marker in rel:
            return "existing_prior"
    return "found"


def _scan_forbidden_files(scan_root: Path) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if not scan_root.is_dir():
        return found
    for fp in scan_root.rglob("*"):
        if not fp.is_file():
            continue
        name = fp.name
        is_forbidden = name in FORBIDDEN_ARTIFACT_NAMES or name.endswith(FORBIDDEN_ARTIFACT_SUFFIXES)
        if name.startswith("initrd") or name.startswith("vmlinuz"):
            is_forbidden = True
        if not is_forbidden:
            continue
        if name.startswith("initrd") or name.startswith("vmlinuz"):
            classification = "existing_prior"
        else:
            classification = _artifact_classification(fp)
        found.append({"path": str(fp), "name": name, "classification": classification})
    return found


def validate_no_real_build_artifacts(
    output_root: str | Path,
    *,
    additional_scan_roots: list[str | Path] | None = None,
) -> dict[str, Any]:
    root = Path(output_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    found: list[dict[str, str]] = []

    scan_roots: list[Path] = []
    if root.is_file():
        scan_roots.append(root.parent)
    elif root.is_dir():
        scan_roots.append(root)

    for extra in additional_scan_roots or []:
        ep = Path(extra).resolve()
        if ep.is_dir() and ep not in scan_roots:
            scan_roots.append(ep)

    if not scan_roots:
        return {
            "ok": True,
            "output_root": str(root),
            "found": [],
            "errors": [],
            "warnings": ["output_root_missing"],
        }

    for scan_root in scan_roots:
        for entry in _scan_forbidden_files(scan_root):
            found.append(entry)
            if entry["classification"] == "found":
                errors.append(f"forbidden_artifact:{entry['path']}")

    return {
        "ok": not errors,
        "output_root": str(root),
        "found": found[:80],
        "errors": errors,
        "warnings": warnings,
    }


def _developer_section(dev_validation: dict[str, Any]) -> dict[str, Any]:
    manifest = dev_validation.get("manifest") or {}
    env = dev_validation.get("environment") or {}
    return {
        "profile_id": manifest.get("profile_id", "rescue_developer_local_lab"),
        "agent_enabled": manifest.get("agent_enabled") is True,
        "agent_mode": manifest.get("agent_mode") or env.get("SETUPHELFER_DEV_AGENT_MODE"),
        "auto_upload": manifest.get("developer_auto_upload") is True
        or env.get("SETUPHELFER_DEV_AGENT_AUTO_UPLOAD", "").lower() == "true",
        "server_url": env.get("SETUPHELFER_DEV_AGENT_SERVER_URL")
        or manifest.get("default_server_url"),
        "ssh_allowed": manifest.get("ssh_allowed") is True,
        "write_actions_allowed": manifest.get("write_actions_allowed") is True,
    }


def _public_guard_section(pub_validation: dict[str, Any]) -> dict[str, Any]:
    manifest = pub_validation.get("manifest") or {}
    env = pub_validation.get("environment") or {}
    agent_enabled = manifest.get("agent_enabled") is True or env.get(
        "SETUPHELFER_DEV_AGENT_ENABLED", ""
    ).lower() == "true"
    auto_upload = manifest.get("developer_auto_upload") is True or env.get(
        "SETUPHELFER_DEV_AGENT_AUTO_UPLOAD", ""
    ).lower() == "true"
    return {
        "agent_enabled": agent_enabled,
        "auto_upload": auto_upload,
        "mode": manifest.get("agent_mode") or env.get("SETUPHELFER_DEV_AGENT_MODE", "public_rescue"),
        "public_upload_safe": not agent_enabled and not auto_upload,
    }


def _systemd_section(developer_profile_root: Path, dev_validation: dict[str, Any]) -> dict[str, Any]:
    svc_path = developer_profile_root / "systemd" / "setuphelfer-dev-agent.service"
    pub_root = developer_profile_root.parent / "public"
    pub_svc = pub_root / "systemd" / "setuphelfer-dev-agent.service"
    svc_text = svc_path.read_text(encoding="utf-8") if svc_path.is_file() else ""
    exec_safe = "devserver_agent.cli" in svc_text and "NoNewPrivileges=true" in svc_text
    return {
        "service": "setuphelfer-dev-agent.service",
        "enabled_in_developer_profile": dev_validation.get("ok", False) and svc_path.is_file(),
        "enabled_in_public_profile": pub_svc.is_file(),
        "exec_start_safe": exec_safe,
        "no_new_privileges": "NoNewPrivileges=true" in svc_text,
    }


def validate_rescue_developer_iso_dry_build(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = list(manifest.get("errors") or [])
    warnings: list[str] = list(manifest.get("warnings") or [])

    if manifest.get("real_iso_build") is True:
        errors.append("real_iso_build_must_be_false")
    if manifest.get("generated_iso") is True:
        errors.append("generated_iso_must_be_false")

    dev = manifest.get("developer_profile") or {}
    pub = manifest.get("public_profile_guard") or {}
    forbidden = manifest.get("forbidden_artifacts") or {}

    if not dev.get("agent_enabled"):
        errors.append("developer_agent_not_enabled")
    if dev.get("agent_mode") != "local_lab":
        errors.append("developer_mode_not_local_lab")
    if not dev.get("auto_upload"):
        errors.append("developer_auto_upload_not_true")
    if dev.get("ssh_allowed"):
        errors.append("developer_ssh_allowed")
    if dev.get("write_actions_allowed"):
        errors.append("developer_write_actions_allowed")

    if pub.get("agent_enabled"):
        errors.append("public_agent_enabled")
    if pub.get("auto_upload"):
        errors.append("public_auto_upload_enabled")
    if not pub.get("public_upload_safe"):
        errors.append("public_profile_not_safe")

    if forbidden.get("iso") or forbidden.get("img") or forbidden.get("squashfs") or forbidden.get("chroot"):
        errors.append("forbidden_artifacts_present")

    status = "blocked" if errors else ("review_required" if warnings else "ok")
    return {
        "status": status,
        "ok": status == "ok",
        "errors": errors,
        "warnings": warnings,
    }


def build_rescue_developer_iso_dry_build_manifest(
    developer_profile_root: str,
    public_profile_root: str | None,
    output_path: str,
) -> dict[str, Any]:
    dev_root = Path(developer_profile_root).resolve()
    pub_root = Path(public_profile_root).resolve() if public_profile_root else None

    dev_validation = validate_developer_profile(dev_root)
    pub_validation = validate_public_profile_guard(pub_root)

    placement = build_agent_profile_placement_plan(dev_root)
    out_file = Path(output_path).resolve()
    repo = _repo_root()
    artifact_scan = validate_no_real_build_artifacts(
        out_file.parent,
        additional_scan_roots=[repo / "build" / "rescue"],
    )

    warnings: list[str] = []
    errors: list[str] = []

    if not dev_validation.get("ok"):
        errors.extend(dev_validation.get("errors") or [])
    warnings.extend(dev_validation.get("warnings") or [])

    if not pub_validation.get("ok"):
        errors.extend(pub_validation.get("errors") or [])
    warnings.extend(pub_validation.get("warnings") or [])

    if not artifact_scan.get("ok"):
        errors.extend(artifact_scan.get("errors") or [])
    warnings.extend(artifact_scan.get("warnings") or [])

    prior_count = sum(
        1 for item in (artifact_scan.get("found") or [])
        if item.get("classification") == "existing_prior"
    )
    if prior_count:
        warnings.append(f"prior_iso_artifacts_in_tree:{prior_count}")

    forbidden_flags = {
        "iso": any(
            (item.get("name") or "").endswith(".iso") and item.get("classification") == "found"
            for item in (artifact_scan.get("found") or [])
        ),
        "img": any(
            (item.get("name") or "").endswith(".img") and item.get("classification") == "found"
            for item in (artifact_scan.get("found") or [])
        ),
        "squashfs": any(
            item.get("name") == "filesystem.squashfs" and item.get("classification") == "found"
            for item in (artifact_scan.get("found") or [])
        ),
        "chroot": False,
    }

    manifest: dict[str, Any] = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "status": "ok",
        "dry_build": True,
        "real_iso_build": False,
        "generated_iso": False,
        "developer_profile": _developer_section(dev_validation),
        "public_profile_guard": _public_guard_section(pub_validation),
        "systemd": _systemd_section(dev_root, dev_validation),
        "placement_plan": placement,
        "forbidden_artifacts": forbidden_flags,
        "artifact_scan": {
            "prior_artifacts_count": prior_count,
            "new_forbidden_count": len(artifact_scan.get("errors") or []),
        },
        "profile_validation": {
            "developer": {"ok": dev_validation.get("ok"), "errors": dev_validation.get("errors")},
            "public_guard": {"ok": pub_validation.get("ok"), "errors": pub_validation.get("errors")},
        },
        "warnings": warnings,
        "errors": errors,
    }

    validation = validate_rescue_developer_iso_dry_build(manifest)
    manifest["status"] = validation["status"]
    manifest["errors"] = validation["errors"]
    manifest["warnings"] = list(dict.fromkeys(validation["warnings"]))

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return manifest
