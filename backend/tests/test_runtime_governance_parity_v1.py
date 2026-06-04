"""Parity between governance bundle and legacy install_profile helpers."""

from __future__ import annotations

import os
from unittest.mock import patch

from core.install_profile import _capabilities_for_profile, get_install_profile_state
from runtime_governance.profile_policy import _base_capabilities_for_profile_name
from runtime_governance.service import resolve_runtime_governance_bundle


def test_capabilities_matrix_parity():
    for profile_name in ("release", "local_lab", "developer", "rescue_lab", "production"):
        legacy = _capabilities_for_profile(profile_name)
        canonical = _base_capabilities_for_profile_name(profile_name)
        assert legacy == canonical, profile_name


def test_state_parity_release():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
        bundle = resolve_runtime_governance_bundle()
        st = get_install_profile_state()
        assert st.install_profile == bundle.profile.name
        assert st.dev_control_enabled == bundle.capabilities.dev_control_enabled
        assert st.dev_server_enabled == bundle.capabilities.dev_server_enabled
