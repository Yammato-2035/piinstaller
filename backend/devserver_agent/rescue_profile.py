"""Rescue Developer Edition profile validation (dry-run, no ISO build)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from devserver_agent.config import validate_server_url

FORBIDDEN_TOKENS = frozenset({
    "dd", "mkfs", "mount", "umount", "parted", "sfdisk", "sgdisk", "wipefs",
    "apt", "sudo", "rm -rf", "debootstrap", "lb build", "chroot",
})

SECRET_KEY_RE = re.compile(
    r"(token|secret|password|api_key|private_key)\s*=",
    re.I,
)

WRITE_KEY_RE = re.compile(
    r"(write_actions_allowed|backup|restore|repair|ssh_allowed)\s*=\s*true",
    re.I,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def default_developer_profile_root(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "build" / "rescue" / "profiles" / "developer"


def default_public_profile_root(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "build" / "rescue" / "profiles" / "public"


def default_developer_qemu_profile_root(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "build" / "rescue" / "profiles" / "developer-qemu"


def _read_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" in s:
            k, _, v = s.partition("=")
            out[k.strip()] = v.strip()
    return out


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _scan_text_for_violations(text: str, *, context: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    lowered = text.lower()
    for token in FORBIDDEN_TOKENS:
        if token in lowered:
            errors.append(f"{context}:forbidden_token:{token}")
    if SECRET_KEY_RE.search(text):
        errors.append(f"{context}:secret_or_token_key")
    if WRITE_KEY_RE.search(text):
        errors.append(f"{context}:write_or_ssh_enabled")
    return errors, warnings


def build_developer_profile_manifest(profile_root: str | Path) -> dict[str, Any]:
    root = Path(profile_root).resolve()
    manifest_path = root / "manifest.json"
    manifest = _read_manifest(manifest_path)
    env = _read_env_file(root / "environment" / "setuphelfer-dev-agent.env")
    return {
        "profile_root": str(root),
        "manifest": manifest,
        "environment": env,
        "systemd_service": (root / "systemd" / "setuphelfer-dev-agent.service").is_file(),
    }


def validate_developer_profile(profile_root: str | Path) -> dict[str, Any]:
    root = Path(profile_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = root / "manifest.json"
    env_path = root / "environment" / "setuphelfer-dev-agent.env"
    service_path = root / "systemd" / "setuphelfer-dev-agent.service"

    if not root.is_dir():
        errors.append("profile_root_missing")
        return {"ok": False, "errors": errors, "warnings": warnings}

    if not manifest_path.is_file():
        errors.append("manifest_missing")
    if not env_path.is_file():
        errors.append("environment_missing")
    if not service_path.is_file():
        errors.append("systemd_service_missing")

    manifest = _read_manifest(manifest_path)
    env = _read_env_file(env_path)

    if manifest.get("agent_enabled") is not True:
        errors.append("agent_not_enabled_in_manifest")
    if manifest.get("agent_mode") != "local_lab":
        errors.append("agent_mode_not_local_lab")
    if manifest.get("developer_auto_upload") is not True:
        errors.append("developer_auto_upload_not_true")
    if manifest.get("ssh_allowed") is True:
        errors.append("ssh_allowed_in_manifest")
    if manifest.get("write_actions_allowed") is True:
        errors.append("write_actions_in_manifest")

    if env.get("SETUPHELFER_DEV_AGENT_ENABLED", "").lower() != "true":
        errors.append("env_agent_not_enabled")
    if env.get("SETUPHELFER_DEV_AGENT_MODE") != "local_lab":
        errors.append("env_mode_not_local_lab")
    if env.get("SETUPHELFER_DEV_AGENT_AUTO_UPLOAD", "").lower() != "true":
        errors.append("env_auto_upload_not_true")

    server_url = env.get("SETUPHELFER_DEV_AGENT_SERVER_URL", "")
    if server_url:
        ok, err = validate_server_url(server_url)
        if not ok:
            errors.append(f"env_server_url_blocked:{err}")

    for path in (env_path, service_path, manifest_path):
        if path.is_file():
            e, w = _scan_text_for_violations(path.read_text(encoding="utf-8"), context=path.name)
            errors.extend(e)
            warnings.extend(w)

    if service_path.is_file():
        svc = service_path.read_text(encoding="utf-8")
        if "NoNewPrivileges=true" not in svc:
            errors.append("systemd_missing_no_new_privileges")
        if "backend.devserver_agent.cli" not in svc:
            errors.append("systemd_missing_agent_cli")
        if "ExecStart=" in svc:
            for line in svc.splitlines():
                if line.strip().startswith("ExecStart=") and "devserver_agent.cli" not in line:
                    errors.append("systemd_execstart_not_agent_cli")

    return {
        "ok": not errors,
        "profile_root": str(root),
        "manifest": manifest,
        "environment": env,
        "errors": errors,
        "warnings": warnings,
    }


def validate_public_profile_guard(profile_root: str | Path | None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if profile_root is None:
        return {
            "ok": True,
            "profile_root": None,
            "errors": [],
            "warnings": ["public_profile_not_materialized"],
        }

    root = Path(profile_root).resolve()
    if not root.is_dir():
        warnings.append("public_profile_root_missing")
        return {"ok": True, "profile_root": str(root), "errors": [], "warnings": warnings}

    env_path = root / "environment" / "setuphelfer-dev-agent.env"
    manifest_path = root / "manifest.json"
    env = _read_env_file(env_path)
    manifest = _read_manifest(manifest_path) if manifest_path.is_file() else {}

    if env.get("SETUPHELFER_DEV_AGENT_ENABLED", "false").lower() == "true":
        errors.append("public_env_agent_enabled")
    if env.get("SETUPHELFER_DEV_AGENT_AUTO_UPLOAD", "false").lower() == "true":
        errors.append("public_auto_upload_enabled")
    if env.get("SETUPHELFER_DEV_AGENT_MODE") == "local_lab":
        errors.append("public_mode_local_lab")

    if manifest.get("developer_auto_upload") is True:
        errors.append("public_manifest_auto_upload")
    if manifest.get("agent_enabled") is True:
        errors.append("public_manifest_agent_enabled")

    server_url = env.get("SETUPHELFER_DEV_AGENT_SERVER_URL", "")
    if server_url:
        ok, err = validate_server_url(server_url)
        if not ok:
            errors.append(f"public_env_server_url_blocked:{err}")

    for path in (env_path, manifest_path):
        if path.is_file():
            e, w = _scan_text_for_violations(path.read_text(encoding="utf-8"), context=path.name)
            errors.extend(e)
            warnings.extend(w)

    return {
        "ok": not errors,
        "profile_root": str(root),
        "environment": env,
        "manifest": manifest,
        "errors": errors,
        "warnings": warnings,
    }


def validate_developer_qemu_profile(profile_root: str | Path) -> dict[str, Any]:
    """Validate Rescue Developer QEMU lab overlay (local_lab, 10.0.2.2, keyboard, remote)."""
    root = Path(profile_root).resolve()
    base = validate_developer_profile(root)
    errors = list(base.get("errors") or [])
    warnings = list(base.get("warnings") or [])

    manifest = base.get("manifest") or {}
    if manifest.get("profile_type") != "developer_qemu":
        errors.append("profile_type_not_developer_qemu")
    if manifest.get("qemu_host_fallback") is not True:
        errors.append("qemu_host_fallback_not_true")

    env = base.get("environment") or {}
    server_url = env.get("SETUPHELFER_DEV_AGENT_SERVER_URL", "")
    if "10.0.2.2" not in server_url:
        errors.append("env_server_url_not_qemu_host")
    if env.get("SETUPHELFER_DEV_AGENT_QEMU_HOST_FALLBACK", "").lower() != "true":
        errors.append("env_qemu_host_fallback_not_true")

    qemu = manifest.get("qemu") if isinstance(manifest.get("qemu"), dict) else {}
    remote = qemu.get("remote_console") if isinstance(qemu.get("remote_console"), dict) else {}
    ssh_fwd = qemu.get("ssh_forward") if isinstance(qemu.get("ssh_forward"), dict) else {}
    keyboard = qemu.get("keyboard") if isinstance(qemu.get("keyboard"), dict) else {}

    if remote.get("public_exposure") is True:
        errors.append("remote_console_public_exposure")
    bind = remote.get("bind")
    if bind is not None and bind != "127.0.0.1":
        errors.append("remote_console_bind_not_localhost")
    if "0.0.0.0" in json.dumps(qemu):
        errors.append("remote_bind_all_interfaces_forbidden")

    if ssh_fwd.get("enabled") is True:
        errors.append("ssh_forward_must_stay_disabled_until_explicit_enable")
    if ssh_fwd.get("bind") not in (None, "127.0.0.1"):
        errors.append("ssh_forward_bind_not_localhost")

    if keyboard.get("qemu_keymap") != "de":
        errors.append("german_keyboard_qemu_keymap_missing")
    if keyboard.get("live_keyboard_layout") != "de":
        errors.append("german_keyboard_live_layout_missing")
    if keyboard.get("locale") != "de_DE.UTF-8":
        errors.append("german_keyboard_locale_missing")
    if keyboard.get("timezone") != "Europe/Berlin":
        errors.append("german_keyboard_timezone_missing")

    return {
        **base,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "qemu": qemu,
    }
