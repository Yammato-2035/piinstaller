"""Dev-server defaults aligned with install profile (single policy source)."""

from __future__ import annotations

import os

from runtime_governance.models import DevServerPolicy, RuntimeCapabilities, RuntimeProfile


def _env_unset(key: str) -> bool:
    raw = os.environ.get(key)
    return raw is None or not str(raw).strip()


def build_devserver_policy(
    profile: RuntimeProfile,
    capabilities: RuntimeCapabilities,
) -> DevServerPolicy:
    if not capabilities.dev_server_enabled:
        try:
            from core.developer_capability import is_dev_server_host_locally_allowed

            if is_dev_server_host_locally_allowed(
                install_profile=profile.name,
                dev_control_enabled=capabilities.dev_control_enabled,
            ):
                enabled: bool | None = None
                mode: str | None = None
                require_token: bool | None = None
                if _env_unset("SETUPHELFER_DEV_SERVER_ENABLED"):
                    enabled = True
                if _env_unset("SETUPHELFER_DEV_SERVER_MODE"):
                    mode = "local_lab"
                if _env_unset("SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN"):
                    require_token = True
                return DevServerPolicy(enabled, mode, require_token)
        except Exception:
            pass
        return DevServerPolicy(None, None, None)
    enabled: bool | None = None
    mode: str | None = None
    require_token: bool | None = None
    if _env_unset("SETUPHELFER_DEV_SERVER_ENABLED"):
        enabled = True
    if _env_unset("SETUPHELFER_DEV_SERVER_MODE"):
        mode = "local_lab"
    if profile.name == "local_lab" and _env_unset("SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN"):
        require_token = False
    return DevServerPolicy(enabled, mode, require_token)
