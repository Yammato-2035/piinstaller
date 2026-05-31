"""Dev Agent server URL resolution with optional QEMU user-NAT fallback."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from devserver_agent.client import health_check, validate_server_health
from devserver_agent.config import DevAgentMode, validate_server_url

DEFAULT_LOCAL_URL = "http://127.0.0.1:8000"
DEFAULT_QEMU_HOST_URL = "http://10.0.2.2:8000"
_KERNEL_URL_RE = re.compile(r"setuphelfer_dev_server_url=(https?://[^\s]+)", re.I)


def is_private_or_local_dev_server_url(url: str) -> bool:
    ok, _ = validate_server_url(url)
    return ok


def is_qemu_guest_hint() -> bool:
    if os.environ.get("SETUPHELFER_DEV_AGENT_QEMU_GUEST_HINT", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True
    dmi = Path("/sys/class/dmi/id/product_name")
    if dmi.is_file():
        name = dmi.read_text(encoding="utf-8", errors="replace").lower()
        if any(x in name for x in ("qemu", "kvm", "virtual", "bochs")):
            return True
    return False


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _kernel_boot_server_url() -> str | None:
    try:
        cmdline = Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = _KERNEL_URL_RE.search(cmdline)
    return _normalize_url(m.group(1)) if m else None


def _probe_health(url: str, mode: DevAgentMode, timeout: float) -> bool:
    if mode == "public_rescue":
        return False
    if not is_private_or_local_dev_server_url(url):
        return False
    hc = health_check(url, timeout=timeout)
    validated = validate_server_health(hc, mode)
    return bool(validated.get("ok"))


def candidate_server_urls(
    *,
    cli_server: str | None = None,
    env_server: str | None = None,
    mode: DevAgentMode = "local_lab",
    qemu_host_fallback: bool = False,
    qemu_host_url: str = DEFAULT_QEMU_HOST_URL,
    include_default_local: bool = True,
) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    def add(url: str, source: str) -> None:
        u = _normalize_url(url)
        if not u or u in seen:
            return
        if not is_private_or_local_dev_server_url(u):
            return
        seen.add(u)
        out.append({"url": u, "source": source})

    if cli_server:
        add(cli_server, "cli")
    if env_server:
        add(env_server, "env")
    boot = _kernel_boot_server_url()
    if boot:
        add(boot, "kernel_cmdline")
    if mode == "local_lab" and qemu_host_fallback:
        add(qemu_host_url, "qemu_user_nat_fallback")
    if include_default_local:
        add(DEFAULT_LOCAL_URL, "default_local")

    return out


def resolve_dev_server_url(
    *,
    cli_server: str | None = None,
    env_server: str | None = None,
    mode: DevAgentMode = "local_lab",
    qemu_host_fallback: bool | None = None,
    qemu_host_url: str | None = None,
    timeout_seconds: float = 5.0,
    probe: bool = True,
) -> dict[str, Any]:
    """Resolve Dev Server URL; probe candidates when probe=True."""
    warnings: list[str] = []
    errors: list[str] = []

    if mode == "public_rescue":
        warnings.append("public_rescue_no_auto_upload")

    q_fallback = (
        qemu_host_fallback
        if qemu_host_fallback is not None
        else _env_bool("SETUPHELFER_DEV_AGENT_QEMU_HOST_FALLBACK", False)
    )
    q_url = _normalize_url(
        qemu_host_url
        or os.environ.get("SETUPHELFER_DEV_AGENT_QEMU_HOST_URL")
        or DEFAULT_QEMU_HOST_URL
    )

    if q_fallback and mode != "local_lab":
        warnings.append("qemu_fallback_ignored_non_local_lab")

    candidates = candidate_server_urls(
        cli_server=cli_server,
        env_server=env_server,
        mode=mode,
        qemu_host_fallback=q_fallback and mode == "local_lab",
        qemu_host_url=q_url,
    )

    probed: list[dict[str, Any]] = []
    selected_url: str | None = None
    selected_source: str | None = None

    for item in candidates:
        url = item["url"]
        source = item["source"]
        reachable = False
        if probe and mode != "public_rescue":
            reachable = _probe_health(url, mode, timeout_seconds)
        probed.append({**item, "reachable": reachable})
        if probe and reachable and selected_url is None:
            selected_url = url
            selected_source = source

    if selected_url is None and candidates and not probe:
        selected_url = candidates[0]["url"]
        selected_source = candidates[0]["source"]

    if selected_url is None and candidates and probe and mode != "public_rescue":
        warnings.append("no_reachable_dev_server_candidate")

    if selected_url and not is_private_or_local_dev_server_url(selected_url):
        errors.append("selected_url_not_private")
        selected_url = None
        selected_source = None

    return {
        "selected_url": selected_url,
        "source": selected_source,
        "candidates": probed,
        "qemu_host_fallback_enabled": q_fallback and mode == "local_lab",
        "qemu_guest_hint": is_qemu_guest_hint(),
        "warnings": warnings,
        "errors": errors,
    }
