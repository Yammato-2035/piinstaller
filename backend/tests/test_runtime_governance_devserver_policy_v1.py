"""Dev-server policy alignment with install profile."""

from __future__ import annotations

import os
from unittest.mock import patch

from devserver.config import load_dev_server_config
from runtime_governance.devserver_policy import build_devserver_policy
from runtime_governance.profile_policy import build_runtime_capabilities, resolve_runtime_profile


def test_local_lab_require_token_default_false():
    with patch.dict(
        os.environ,
        {
            "SETUPHELFER_INSTALL_PROFILE": "local_lab",
            "SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN": "",
            "SETUPHELFER_DEV_SERVER_ENABLED": "",
        },
        clear=False,
    ):
        profile = resolve_runtime_profile()
        cap = build_runtime_capabilities(profile)
        policy = build_devserver_policy(profile, cap)
        assert policy.require_token_default is False
        cfg = load_dev_server_config()
        assert cfg.require_token is False


def test_release_devserver_disabled():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
        profile = resolve_runtime_profile()
        cap = build_runtime_capabilities(profile)
        policy = build_devserver_policy(profile, cap)
        assert policy.enabled_default is None
