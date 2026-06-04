"""Runtime governance profile and capability contracts."""

from __future__ import annotations

import os
from unittest.mock import patch

from runtime_governance.profile_policy import (
    build_runtime_capabilities,
    resolve_runtime_profile,
)
from runtime_governance.service import materialize_install_profile_state


def test_release_capabilities():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
        profile = resolve_runtime_profile()
        cap = build_runtime_capabilities(profile)
        assert profile.name == "release"
        assert cap.dev_control_enabled is False
        assert cap.dev_server_enabled is False
        assert cap.fleet_sessions_enabled is False


def test_local_lab_capabilities():
    with patch.dict(
        os.environ,
        {
            "SETUPHELFER_INSTALL_PROFILE": "local_lab",
            "SETUPHELFER_DEV_CONTROL_ENABLED": "",
            "SETUPHELFER_DEV_SERVER_ENABLED": "",
        },
        clear=False,
    ):
        profile = resolve_runtime_profile()
        cap = build_runtime_capabilities(profile)
        assert profile.name == "local_lab"
        assert cap.dev_control_enabled is True
        assert cap.dev_server_enabled is True
        assert cap.fleet_sessions_enabled is True


def test_invalid_profile_fallback_release():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "not_a_profile"}, clear=False):
        profile = resolve_runtime_profile()
        assert profile.name == "release"
        assert profile.source == "invalid_profile_fallback_release"


def test_materialize_matches_legacy_state_fields():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=False):
        st = materialize_install_profile_state()
        assert st.install_profile == "local_lab"
        assert st.dev_control_enabled is True
        assert st.dev_server_enabled is True
