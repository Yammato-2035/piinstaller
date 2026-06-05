"""Route exposure under release vs local_lab."""

from __future__ import annotations

import os
from unittest.mock import patch

from core.install_profile import path_allowed_for_active_profile
from runtime_governance.route_exposure import decide_route_exposure
from runtime_governance.service import resolve_runtime_governance_bundle


def test_release_blocks_fleet():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
        bundle = resolve_runtime_governance_bundle()
        d = decide_route_exposure("/api/fleet/sessions", bundle.capabilities)
        assert d.allowed is False
        assert d.block_code == "PROFILE_ROUTE_BLOCKED"
        assert path_allowed_for_active_profile("/api/fleet/sessions") is False


def test_local_lab_allows_fleet():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=False):
        bundle = resolve_runtime_governance_bundle()
        d = decide_route_exposure("/api/fleet/sessions", bundle.capabilities)
        assert d.allowed is True
        assert path_allowed_for_active_profile("/api/fleet/sessions") is True


def test_release_allows_rescue_telemetry_not_dcc():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
        bundle = resolve_runtime_governance_bundle()
        for path in (
            "/api/rescue/telemetry/health",
            "/api/rescue/telemetry/v1/ingest",
        ):
            d = decide_route_exposure(path, bundle.capabilities)
            assert d.allowed is True
            assert d.block_code is None
            assert path_allowed_for_active_profile(path) is True
        dcc = decide_route_exposure("/api/dev-dashboard/status", bundle.capabilities)
        assert dcc.allowed is False
        assert dcc.block_code == "PROFILE_ROUTE_BLOCKED"
