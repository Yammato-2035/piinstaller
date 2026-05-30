"""Konfiguration für den Setuphelfer Development Agent."""

from __future__ import annotations

import ipaddress
import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

DevAgentMode = Literal["public_rescue", "beta_opt_in", "local_lab"]

_VALID_MODES: frozenset[str] = frozenset({"public_rescue", "beta_opt_in", "local_lab"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _is_allowed_server_host(host: str) -> bool:
    h = (host or "").strip().lower()
    if h in {"127.0.0.1", "localhost", "::1"}:
        return True
    try:
        addr = ipaddress.ip_address(h)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        pass
    try:
        resolved = socket.getaddrinfo(h, None)
        for entry in resolved:
            ip = entry[4][0]
            try:
                addr = ipaddress.ip_address(ip)
                if not (addr.is_private or addr.is_loopback or addr.is_link_local):
                    return False
            except ValueError:
                return False
        return bool(resolved)
    except OSError:
        return False


def validate_server_url(url: str) -> tuple[bool, str | None]:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"}:
        return False, "invalid_scheme"
    host = parsed.hostname
    if not host:
        return False, "missing_host"
    if not _is_allowed_server_host(host):
        return False, "public_domain_blocked"
    return True, None


@dataclass(frozen=True)
class DevAgentConfig:
    enabled: bool
    mode: DevAgentMode
    server_url: str
    token: str | None
    node_id: str
    display_name: str
    auto_upload: bool
    spool_dir: Path
    timeout_seconds: float
    collect_storage: bool
    collect_boot: bool
    collect_hardware: bool
    repo_root: Path

    @property
    def upload_allowed(self) -> bool:
        if not self.enabled:
            return False
        if self.mode == "public_rescue":
            return False
        if self.mode == "local_lab":
            return self.auto_upload
        if self.mode == "beta_opt_in":
            return self.auto_upload
        return False


def load_dev_agent_config(*, repo_root: Path | None = None) -> DevAgentConfig:
    root = repo_root or _repo_root()
    enabled = _env_bool("SETUPHELFER_DEV_AGENT_ENABLED", False)
    mode_raw = (os.environ.get("SETUPHELFER_DEV_AGENT_MODE") or "public_rescue").strip().lower()
    mode: DevAgentMode = mode_raw if mode_raw in _VALID_MODES else "public_rescue"  # type: ignore[assignment]

    server_url = (os.environ.get("SETUPHELFER_DEV_AGENT_SERVER_URL") or "http://127.0.0.1:8000").strip().rstrip("/")
    token = (os.environ.get("SETUPHELFER_DEV_AGENT_TOKEN") or "").strip() or None
    node_id = (os.environ.get("SETUPHELFER_DEV_AGENT_NODE_ID") or "").strip()
    display_name = (os.environ.get("SETUPHELFER_DEV_AGENT_DISPLAY_NAME") or "").strip()
    auto_upload = _env_bool("SETUPHELFER_DEV_AGENT_AUTO_UPLOAD", False)

    if mode == "public_rescue":
        auto_upload = False

    spool_rel = (
        os.environ.get("SETUPHELFER_DEV_AGENT_SPOOL_DIR")
        or "docs/evidence/runtime-results/dev-agent-spool"
    ).strip()
    spool_dir = Path(spool_rel)
    if not spool_dir.is_absolute():
        spool_dir = (root / spool_dir).resolve()

    try:
        timeout_seconds = float(os.environ.get("SETUPHELFER_DEV_AGENT_TIMEOUT_SECONDS", "5"))
    except ValueError:
        timeout_seconds = 5.0

    return DevAgentConfig(
        enabled=enabled,
        mode=mode,
        server_url=server_url,
        token=token,
        node_id=node_id,
        display_name=display_name,
        auto_upload=auto_upload,
        spool_dir=spool_dir,
        timeout_seconds=max(1.0, min(timeout_seconds, 60.0)),
        collect_storage=_env_bool("SETUPHELFER_DEV_AGENT_COLLECT_STORAGE", True),
        collect_boot=_env_bool("SETUPHELFER_DEV_AGENT_COLLECT_BOOT", True),
        collect_hardware=_env_bool("SETUPHELFER_DEV_AGENT_COLLECT_HARDWARE", True),
        repo_root=root,
    )
