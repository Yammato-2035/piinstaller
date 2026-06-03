"""Konfiguration für den Setuphelfer Development Server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DevServerMode = Literal["disabled", "local_lab"]

_VALID_MODES: frozenset[str] = frozenset({"disabled", "local_lab"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DevServerConfig:
    enabled: bool
    mode: DevServerMode
    storage_root: Path
    allow_remote_ssh: bool
    bind_hint: str
    accept_public_uploads: bool
    require_token: bool
    token_env: str
    repo_root: Path
    auth_token_value: str | None

    @property
    def token(self) -> str | None:
        if not self.require_token:
            return None
        return self.auth_token_value

    @property
    def ssh_allowed(self) -> bool:
        return self.enabled and self.mode == "local_lab" and self.allow_remote_ssh

    @property
    def public_uploads_allowed(self) -> bool:
        return self.enabled and self.accept_public_uploads


def _profile_dev_server_defaults() -> tuple[bool | None, DevServerMode | None, bool | None]:
    """Align Dev Server runtime config with install profile when env omits explicit values."""
    try:
        from core.install_profile import get_install_profile_state

        st = get_install_profile_state()
    except Exception:
        return None, None, None
    if not st.dev_server_enabled:
        return None, None, None
    enabled: bool | None = None
    mode: DevServerMode | None = None
    require_token: bool | None = None
    if os.environ.get("SETUPHELFER_DEV_SERVER_ENABLED") is None:
        enabled = True
    if os.environ.get("SETUPHELFER_DEV_SERVER_MODE") is None:
        mode = "local_lab"
    if st.install_profile == "local_lab" and os.environ.get("SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN") is None:
        require_token = False
    return enabled, mode, require_token


def load_dev_server_config(*, repo_root: Path | None = None) -> DevServerConfig:
    root = repo_root or _repo_root()
    profile_enabled, profile_mode, profile_require_token = _profile_dev_server_defaults()
    enabled = _env_bool("SETUPHELFER_DEV_SERVER_ENABLED", profile_enabled if profile_enabled is not None else False)
    mode_raw = (os.environ.get("SETUPHELFER_DEV_SERVER_MODE") or (profile_mode or "disabled")).strip().lower()
    mode: DevServerMode = "local_lab" if mode_raw == "local_lab" else "disabled"
    if mode not in _VALID_MODES:
        mode = "disabled"
    if not enabled:
        mode = "disabled"

    storage_rel = (
        os.environ.get("SETUPHELFER_DEV_SERVER_STORAGE_ROOT")
        or "docs/evidence/runtime-results/dev-server"
    ).strip()
    storage_root = Path(storage_rel)
    if not storage_root.is_absolute():
        storage_root = (root / storage_root).resolve()

    require_token_default = profile_require_token if profile_require_token is not None else True
    require_token = _env_bool("SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN", require_token_default)
    token_env = (os.environ.get("SETUPHELFER_DEV_SERVER_TOKEN_ENV") or "SETUPHELFER_DEV_SERVER_TOKEN").strip()
    auth_token_value: str | None = None
    if require_token:
        auth_token_value = (os.environ.get(token_env) or "").strip() or None

    return DevServerConfig(
        enabled=enabled,
        mode=mode,
        storage_root=storage_root,
        allow_remote_ssh=_env_bool("SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH", False),
        bind_hint=(os.environ.get("SETUPHELFER_DEV_SERVER_BIND_HINT") or "127.0.0.1").strip(),
        accept_public_uploads=_env_bool("SETUPHELFER_DEV_SERVER_ACCEPT_PUBLIC_UPLOADS", False),
        require_token=require_token,
        token_env=token_env,
        repo_root=root,
        auth_token_value=auth_token_value,
    )
