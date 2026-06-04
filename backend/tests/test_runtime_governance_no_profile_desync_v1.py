"""Single governance bundle: profile, capabilities, devserver policy stay aligned."""

from __future__ import annotations

import os
from unittest.mock import patch

from devserver.config import load_dev_server_config
from runtime_governance.devserver_policy import build_devserver_policy
from runtime_governance.service import materialize_install_profile_state, resolve_runtime_governance_bundle


def test_local_lab_no_desync():
    with patch.dict(
        os.environ,
        {
            "SETUPHELFER_INSTALL_PROFILE": "local_lab",
            "SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN": "",
        },
        clear=False,
    ):
        bundle = resolve_runtime_governance_bundle()
        st = materialize_install_profile_state()
        policy = build_devserver_policy(bundle.profile, bundle.capabilities)
        cfg = load_dev_server_config()
        assert st.install_profile == bundle.profile.name == "local_lab"
        assert st.dev_control_enabled == bundle.capabilities.dev_control_enabled is True
        assert st.dev_server_enabled == bundle.capabilities.dev_server_enabled is True
        assert policy.require_token_default is False
        assert cfg.enabled is True
        assert cfg.require_token is False
